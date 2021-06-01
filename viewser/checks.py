
        
import functools
from importlib.metadata import version
import re
import json
import logging
from . import exceptions, remotes

logger = logging.getLogger(__name__)

class WrongVersion(Exception):
    """
    Raised when remotes call for a different major version than the one currently installed
    """

def check_remote_version(remotes_api: remotes.Api):
    """
    Used to decorate operations that connect to remote API(s).  The remotes
    should define a "handshake" path, which should return json containing a
    "viewser_version" field.
    """
    logger.debug("Checking remote version")
    rsp = remotes_api.http("GET", ("",), {})
    if rsp.status_code != 200:
        raise exceptions.ConfigurationError(
                f"The handshake endpoint returned {rsp.status_code}. "
                "Is the handshake URL {url} correct?"
                )
    try:
        remote_version = rsp.json()["viewser_version"]
    except (json.JSONDecodeError,KeyError) as e:
        raise exceptions.ConfigurationError(
                "The handshake endpoint did not return the right data. "
                f"Is the handshake URL correct? {remotes_api.url('')}"
                ) from e

    try:
        assert re.search(r"[0-9]+\.[0-9]+\.[0-9]+",remote_version)
    except AssertionError as ae:
        raise remotes.RemoteError(
                "Handshake version wrong format: {remote_version} (expected n.n.n)"
                ) from ae

    major_version = lambda x: x.split(".")[0]

    logger.debug(f"%s vs %s",remote_version, version("viewser"))
    if not major_version(remote_version) == major_version(version("viewser")):
        raise WrongVersion(
                "Viewser installation has wrong major version. "
                f"Local={version('viewser')} / Remote={remote_version}"
                )
