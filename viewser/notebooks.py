from contextlib import closing
import os
import io
from pymonad.maybe import Maybe
import docker

def run_notebook_server(
        registry: str,
        repository,
        version: str,
        requirements_file: Maybe[io.BufferedReader],
        working_directory: str):

    with closing(docker.client.from_env()) as client:
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

        print(f"{registry}/{repository}:{version}")

        img = client.images.pull(registry+"/"+repository, tag = version)
        return client.containers.run(
                img, remove = True, detach = True,
                network_mode = "host",
                volumes = volumes
                )
