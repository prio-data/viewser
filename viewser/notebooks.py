import hashlib
from pprint import pprint as pp
from urllib.parse import urlencode,urlunparse
from operator import add
import random
import logging
from typing import Callable, Set, Dict, Any, Tuple, Optional
from contextlib import closing
import os
from toolz.functoolz import curry, reduce
from pymonad.maybe import Maybe, Nothing, Just
from pymonad.either import Either, Left, Right
import docker
import psutil

START_PORT = 2000
MAX_PORT=9999

logger = logging.getLogger(__name__)


digest = lambda s: hashlib.md5(s.encode()).hexdigest()
generate_token = lambda: digest(reduce(add, [str(random.random()) for i in range(128)]))

occupied_ports:Callable[[], Set[int]] = lambda: {c.laddr.port for c in psutil.net_connections()}
def seek_port(from_port:int) -> Optional[int]:
    if from_port > MAX_PORT:
        return None 
    else:
        return from_port if from_port not in occupied_ports() else seek_port(from_port+1)

def make_url(port:int, token:str, host: str = "0.0.0.0"):
    return urlunparse(("http", f"{host}:{port}","","",urlencode({"token":token}),""))

def notebook_image(registry: str, repository: str, version: str, pull: bool)-> str:
    name = registry + "/" + repository
    if pull:
        logger.info("Getting the viewserspace image (this might take a while...)")
        with closing(docker.client.from_env()) as client:
            client.images.pull(name, tag = version)
    else:
        logger.debug("Using local image")
    return name + ":" + version

def run_notebook_server(
        port: int,
        image: str,
        working_directory: str,
        requirements_file: Maybe[str],
        )-> Tuple[str, str]:

    volumes = {
        os.path.abspath(working_directory):{
            "bind":"/home/views/notebooks",
            "mode": "rw"
            },
        os.path.expanduser("~/.views/config.json"):{
            "bind": "/home/views/.views/config.json",
            "mode": "ro"
            }
        }

    volumes = requirements_file.maybe(volumes, lambda fname: {
            os.path.abspath(fname):{
                "bind": "/home/views/user_requirements.txt",
                "mode": "ro"
                }
        })

    token = generate_token()

    with closing(docker.client.from_env()) as client:
        configuration = {
                "image": image,
                "remove": True,
                "detach": True,
                "volumes" : volumes,
                "environment":{
                    "NOTEBOOK_SERVER_HOST":"0.0.0.0",
                    "NOTEBOOK_SERVER_TOKEN": token,
                    },
                "ports": {
                    "8888/tcp": port
                    }
            }

        container = client.containers.run(**configuration)
        return (container.id, make_url(port, token))
