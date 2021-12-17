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
from . import settings, fetching, remotes, checks, error_handling

logger = logging.getLogger(__name__)

REMOTE_URL = settings.config_get("REMOTE_URL")
REPO_URL = settings.config_get("REPO_URL")

check_pypi_version = curry(
        checks.maybe_log,
        checks.check_pypi_version,
        )

queryset_request = curry(remotes.request, REMOTE_URL+"/querysets")

error_handler = error_handling.ErrorDumper([
        error_handling.FileErrorHandler(settings.ERROR_DUMP_DIRECTORY),
        error_handling.StreamHandler(),
    ])

@check_pypi_version
def fetch(queryset_name:str, start_date: Optional[date] = None, end_date: Optional[date] = None):
    """
    Fetches data for a queryset,
    """
    return (fetching.fetch_queryset(
                settings.config_get("RETRIES"),
                REMOTE_URL,
                queryset_name,
                start_date, end_date
                )
                .either(error_handler.dump, identity)
            )

@check_pypi_version
def list_querysets():
    return (queryset_request("GET", remotes.status_checks, "querysets")
        .then(lambda rsp: rsp.json())
        .either(error_handler.dump, identity)
        )

@check_pypi_version
def show_queryset(name: str):
    return (queryset_request("GET", remotes.status_checks, f"querysets/{name}")
        .then(lambda rsp: rsp.json())
        .either(error_handler.dump, identity)
        )

@check_pypi_version
def publish_queryset(queryset: views_schema.Queryset, overwrite: bool = True):
    return (
            queryset_request(
                    "POST",
                    remotes.status_checks,
                    "querysets",
                    parameters = Just({"overwrite":overwrite}),
                    data = Just(queryset.dict()),
                    )
                .either(error_handler.dump, lambda _: f"Published {queryset.name}")
        )


@check_pypi_version
def delete_queryset(name):
    return (
            queryset_request(
                    "DELETE",
                    remotes.status_checks,
                    f"querysets/{name}",
                    )
                .either(error_handler.dump, lambda _: f"Deleted {name}")
        )

# Aliases
publish = publish_queryset

