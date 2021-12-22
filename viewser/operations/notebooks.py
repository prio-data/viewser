from sys import platform
import time
import webbrowser
import json
import hashlib
from urllib.parse import urlencode,urlunparse
from operator import add
import random
import logging
from typing import Callable, Set, Tuple, Optional, Dict
from contextlib import closing
import os
import requests
import pydantic
from toolz.functoolz import reduce, curry, do
from pymonad.maybe import Maybe
from pymonad.either import Either, Left, Right
import docker
import psutil
from viewser import settings
from viewser.error_handling import exceptions
from viewser.tui import ascii_art

START_PORT = 2000
MAX_PORT=9999

logger = logging.getLogger(__name__)


digest = lambda s: hashlib.md5(s.encode()).hexdigest()
generate_token = lambda: digest(reduce(add, [str(random.random()) for i in range(128)]))

if platform in ["linux","linux2"]:
    occupied_ports:Callable[[], Set[int]] = lambda: {c.laddr.port for c in psutil.net_connections()}
else:
    occupied_ports = set

def seek_port(from_port:int) -> Optional[int]:
    if from_port > MAX_PORT:
        return None
    else:
        return from_port if from_port not in occupied_ports() else seek_port(from_port+1)

def make_url(port:int, token:str, host: str = "0.0.0.0"):
    return urlunparse(("http", f"{host}:{port}","","",urlencode({"token":token}),""))

class ServicePrincipal(pydantic.BaseModel):
    clientId: str
    clientSecret: str

    def login_info(self):
        return {
                "username": self.clientId,
                "password": self.clientSecret
            }

def local_sp() -> Either[str, ServicePrincipal]:
    try:
        sp_file_path = os.path.join(settings.CONFIG_DIR, "sp.json")
        with open(sp_file_path) as f:
            return Right(ServicePrincipal(**json.load(f)))
    except FileNotFoundError:
        return Left(f"Could not find SP file at {sp_file_path}")
    except pydantic.ValidationError:
        return Left(f"SP file at {sp_file_path} is corrupted")

def assure_logged_in(
        client: docker.DockerClient,
        registry:str,
        service_principal: ServicePrincipal)-> Dict[str,str]:
    try:
        logger.info(f"Authenticating to registry {registry} using local credentials")
        return Right(client.login(
                    **service_principal.login_info(),
                    registry = registry))
    except docker.errors.APIError as apie:
        return Left(
                f"Failed to authenticate to registry {registry}.\n"
                "Bad credentials?\n"
                f"Raw error: \"{str(apie.explanation)}\"")

def notebook_image(
        registry: str,
        repository: str,
        version: str,
        pull: bool) -> Either[str,str]:

    name = registry + "/" + repository

    if pull:
        logger.info("Refreshing docker image (this might take a while...)")
        with closing(docker.client.from_env()) as client:
            return (local_sp()
                .then(curry(assure_logged_in,client,registry))
                .then(lambda _: Right(client.images.pull(name, tag = version)))
                .then(curry(do,lambda img: logger.info(f"Using {img.short_id}")))
                .then(lambda img: Right(img.tags[0]))
                )
    else:
        tagged_name = name + ":" + version
        return Right(tagged_name)

def run_notebook_server(
        port: int,
        working_directory: str,
        requirements_file: Maybe[str],
        image: str,
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
            os.path.abspath(fname): {
                "bind": "/home/views/user_requirements.txt",
                "mode": "ro"
                }, **volumes
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

def watch(browser: bool, echo: Callable[[str],None], run_report: Tuple[str, str])-> None:
    container_id, container_url = run_report
    echo("Booting up...")

    status_code = -1
    with closing(docker.client.from_env()) as docker_client:
        container = docker_client.containers.get(container_id)
        for line in container.attach(stream = True):
            if status_code != 200:
                print(line.decode())
                try:
                    status_code = requests.get(container_url).status_code
                except requests.ConnectionError:
                    status_code = -1
            else:
                break

        echo("Made connection, checking container status...")
        try:
            time.sleep(1)
            print(docker_client.containers.get(container_id))
        except docker.errors.NotFound:
            raise exceptions.ViewserspaceError(
                    "Container failed to launch",
                    hint = (
                        "This was probably due to a failed dependency download. "
                        "Check the logs above."
                        )
                    )
        else:
            echo("Container OK!")

    echo(ascii_art.VIEWSERSPACE_LOGO)
    echo("Server running. Ctrl-C to stop.")

    if browser:
        webbrowser.open(container_url)
    else:
        echo(f"To access, open {container_url}")

    try:
        while True:
            pass
    finally:
        container = docker.client.from_env().containers.get(container_id)
        container.kill()
