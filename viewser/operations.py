"""
High-level operations intended for users
"""
from datetime import date
from typing import Optional
import logging
import time
from toolz.functoolz import curry
from requests import HTTPError
import views_schema
from . import settings,crud,remotes,checks

logger = logging.getLogger(__name__)

remotes_api = remotes.Api(settings.config_get("REMOTE_URL"),{})

def publish(queryset: views_schema.Queryset):
    """
    Publishes a queryset to the ViEWSER databases, which can then be fetched
    by calling `viewser.operations.fetch(queryset.name)`
    """

    try:
        crud.post_queryset(remotes_api, queryset)
    except HTTPError as httpe:
        logger.info("Queryset named \"%s\" exists, updating",
                queryset.name
            )
    else:
        return

    try:
        crud.update_queryset(remotes_api, queryset)
    except HTTPError as httpe:
        logger.critical("Update returned %s: %s",
                str(httpe.response.status_code),
                str(httpe.response.content),
            )

def fetch(queryset_name:str, start_date: Optional[date] = None, end_date: Optional[date] = None):
    """
    Fetches data for a queryset,
    """
    retries = 0
    while retries < settings.config_get("RETRIES"):
        try:
            return crud.fetch_queryset(remotes_api, queryset_name, start_date, end_date)
        except remotes.OperationPending:
            logger.info("Queryset \"%s\" is being compiled... (%s retries)",
                    queryset_name, str(retries)
                    )
            retries += 1
            time.sleep(settings.config_get("RETRY_FREQUENCY"))

post_queryset = checks.check_remote_version(remotes_api)(
        curry(crud.post_queryset, remotes_api)
    )

put_queryset = checks.check_remote_version(remotes_api)(
        curry(crud.put_queryset, remotes_api)
    )

list_querysets = checks.check_remote_version(remotes_api)(
        curry(crud.list_querysets, remotes_api)
    )

delete_queryset = checks.check_remote_version(remotes_api)(
        curry(crud.delete_queryset, remotes_api)
    )

show_queryset = checks.check_remote_version(remotes_api)(
        curry(crud.show_queryset, remotes_api)
    )
