import subprocess
from typing import Callable
from importlib.metadata import version
import re
import json
import logging
import functools
import requests

from toolz.functoolz import curry, compose
from pymonad.maybe import Just,Nothing,Maybe
from pymonad.either import Either, Left, Right
from . import remotes

logger = logging.getLogger(__name__)

async def log_after(function):
    result = await function()
    result.then(logger.warning)

def maybe_log(check_fn: Callable[[], Maybe[str]], fn):
    """
    Function decorator that might emit a warning log message, if test_fn
    returns Just(str)

    Arguments are passed to test_fn
    """
    @functools.wraps(fn)
    def inner(*args,**kwargs):
        check_fn().then(logger.warning)
        return fn(*args,**kwargs)
    return inner

async def check_server_version(url)-> Maybe[str]:
    """
    Used to decorate operations that connect to remote API(s).  The remotes
    should define a "handshake" path, which should return json containing a
    "viewser_version" field.
    """
    add_header = lambda x: "Error while checking remote version\n" + x

    def check(response: requests.Response):
        try:
            remote_version = response.json()["viewser_version"]
        except (json.JSONDecodeError,KeyError):
            return Just("The handshake endpoint did not return the right data. "
                    "Expected JSON  wiith a 'viewser_version' key, got "
                    f"{response.content.decode()}"
                    )

        try:
            assert re.search(r"[0-9]+\.[0-9]+\.[0-9]+",remote_version)
        except AssertionError:
            return Just("Handshake version wrong format: {remote_version} (expected n.n.n)")

        major_version = lambda x: x.split(".")[0]

        logger.debug("%s vs %s",remote_version, version("viewser"))
        if not major_version(remote_version) == major_version(version("viewser")):
            return Just(
                    "Viewser installation has wrong major version. "
                    f"Local is {version('viewser')} while expected is {remote_version}. "
                    "Please install the correct version by running "
                    f"pip install --upgrade viewser~={remote_version}"
                )
        return Nothing

    return (remotes.request(
            url,
            "GET",
            [curry(remotes.check_content_type,"application/json")] + remotes.status_checks,
            "")
            .either(
                compose(Just,add_header,str),
                compose(lambda m: m.then(add_header),check)
                )
        )

def get_pypi_version() -> Either[str,str]:
    with subprocess.Popen(["pip","show","viewser"],
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE) as proc:
        out,err = proc.communicate()
        if not err:
            version_line,*_ = [l for l in out.split(b"\n") if b"Version" in l]
            return Right(version_line.split()[-1].decode())
        else:
            return Left(err)

def maybe_version_number(raw: str)-> Either[str,str]:
    if re.search(r"[0-9]+\.[0-9]+\.[0-9]+",raw):
        return Right(raw)
    else:
        return Left(f"{raw} is not a version number")

def check_pypi_version() -> Maybe[str]:
    """
    Gets the latest version of the CLI from Github
    """
    logger.debug("checking viewser version on PyPi")
    def version_check(latest)->Maybe[str]:
        current = version("viewser")
        if not latest == current:
            return Just(
                    "There is a newer version of viewser available! "
                    f"You are currently on {current}, but the "
                    f"latest version is {latest}. Please update by "
                    "running pip install --upgrade viewser."
                )
        return Nothing

    return (get_pypi_version()
        .either(compose(Just,str), version_check)
        )
