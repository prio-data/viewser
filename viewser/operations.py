"""
High-level operations intended for users
"""
from datetime import date
from typing import Optional
import logging
import time
from toolz.functoolz import curry, identity
from pymonad.maybe import Just
import views_schema
from . import settings, fetching, remotes, checks, exceptions

logger = logging.getLogger(__name__)

REMOTE_URL = settings.config_get("REMOTE_URL")
REPO_URL = settings.config_get("REPO_URL")

check_pypi_version = curry(
        checks.maybe_log,
        checks.check_pypi_version,
        )

json_status_checks = [curry(remotes.check_content_type,"application/json")] + remotes.status_checks

queryset_request = curry(remotes.request, REMOTE_URL+"/querysets")

@check_pypi_version
def fetch(queryset_name:str, start_date: Optional[date] = None, end_date: Optional[date] = None):
    """
    Fetches data for a queryset,
    """
    retries = 0
    while retries < settings.config_get("RETRIES"):
        try:
            return (fetching.fetch_queryset(
                        REMOTE_URL,
                        queryset_name,
                        start_date, end_date
                        )
                        .either(exceptions.raise_pretty_exception, identity)
                    )
        except exceptions.OperationPending:
            logger.info("Queryset \"%s\" is being compiled... (%s retries)",
                    queryset_name, str(retries)
                    )
            retries += 1
            time.sleep(settings.config_get("RETRY_FREQUENCY"))

@check_pypi_version
def list_querysets():
    return (queryset_request("GET", json_status_checks, "querysets")
        .then(lambda rsp: rsp.json())
        .either(exceptions.raise_pretty_exception, identity)
        )

@check_pypi_version
def show_queryset(name: str):
    return (queryset_request("GET", json_status_checks, f"querysets/{name}")
        .then(lambda rsp: rsp.json())
        .either(exceptions.raise_pretty_exception, identity)
        )

@check_pypi_version
def publish_queryset(queryset: views_schema.Queryset, overwrite: bool = True):
    return (
            queryset_request(
                    "POST",
                    json_status_checks,
                    "querysets",
                    parameters = Just({"overwrite":overwrite}),
                    data = Just(queryset.dict()),
                    )
                .then(lambda rsp: rsp.json())
                .either(exceptions.raise_pretty_exception, identity)
        )


@check_pypi_version
def delete_queryset(name):
    return (
            queryset_request(
                    "DELETE",
                    remotes.status_checks,
                    f"querysets/{name}",
                    )
                .either(exceptions.raise_pretty_exception, lambda _: f"Deleted {name}")
        )

# Aliases
publish = publish_queryset

