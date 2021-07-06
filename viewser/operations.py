"""
High-level operations intended for users
"""
from functools import wraps
from importlib.metadata import version
from datetime import date
from typing import Optional
import logging
import time
from toolz.functoolz import curry, identity
import views_schema
from . import settings,crud,remotes,checks,exceptions

logger = logging.getLogger(__name__)



remotes_api = remotes.Api(settings.config_get("REMOTE_URL"), settings.REMOTE_PATHS)

REMOTE_URL = settings.config_get("REMOTE_URL")
queryset_request = curry(remotes.request, REMOTE_URL+"/querysets")

if not settings.config_get("REMOTE_URL"):
    def raises(*args,**kwargs):
        raise exceptions.ConfigurationError(
                "Tried calling the API without setting the REMOTE_URL configuration setting.",
                hint = "Did you configure viewser? Try running `viewser config interactive`."
            )
    remotes_api.http = raises
    api_request = raises

get_latest_version = curry(remotes.latest_pyproject_version, settings.config_get("REPO_URL"))
check_remote_version = curry(checks.check_remote_version, remotes_api)

def raise_pretty_exception(x: Exception):
    try:
        raise x
    except exceptions.OperationPending:
        raise x
    else:
        raise exceptions.ViewsError(message = str(x))

def check_latest_version():
    latest_known = settings.config_get("LATEST_KNOWN_VERSION")
    latest_actual = get_latest_version()
    current = version("viewser")

    if latest_known < latest_actual:
        settings.config_set_in_file("LATEST_KNOWN_VERSION",latest_actual)

    if current < latest_actual:
        logger.warning(
                f"There is a newer version of viewser available ({latest_actual}), "
                "download with pip install --upgrade viewser. "
                f"Current version is {current}."
                )
    else:
        logger.debug("Up to date!")


def check_remotes(fn):
    """
    Wrapper used for version checking when calling remote APIs
    """
    @wraps(fn)
    def inner(*args,**kwargs):
        check_latest_version()
        check_remote_version()
        return fn(*args,**kwargs)
    return inner

def publish(queryset: views_schema.Queryset, overwrite: bool = True):
    """
    Publishes a queryset to the ViEWSER databases, which can then be fetched
    by calling `viewser.operations.fetch(queryset.name)`
    """
    crud.post_queryset(remotes_api, queryset, overwrite = overwrite)

def fetch(queryset_name:str, start_date: Optional[date] = None, end_date: Optional[date] = None):
    """
    Fetches data for a queryset,
    """
    retries = 0
    while retries < settings.config_get("RETRIES"):
        try:
            return (crud.fetch_queryset(
                        settings.config_get("REMOTE_URL"),
                        queryset_name,
                        start_date, end_date
                        )
                        .either(raise_pretty_exception, identity)
                    )
        except exceptions.OperationPending:
            logger.info("Queryset \"%s\" is being compiled... (%s retries)",
                    queryset_name, str(retries)
                    )
            retries += 1
            time.sleep(settings.config_get("RETRY_FREQUENCY"))

json_status_checks = [curry(remotes.check_content_type,"application/json")] + remotes.status_checks

def list_querysets():
    return (queryset_request("GET", json_status_checks, "querysets")
        .then(lambda rsp: rsp.json())
        .either(raise_pretty_exception, identity)
        )

def show_queryset(name: str):
    return (queryset_request("GET", json_status_checks, f"querysets/{name}")
        .then(lambda rsp: rsp.json())
        .either(raise_pretty_exception, identity)
        )

api_call = lambda fn: check_remotes(curry(fn, remotes_api))
post_queryset = api_call(crud.post_queryset)
put_queryset = api_call(crud.put_queryset)
#list_querysets = api_call(crud.list_querysets)
#show_queryset = api_call(crud.show_queryset)
delete_queryset = api_call(crud.delete_queryset)
