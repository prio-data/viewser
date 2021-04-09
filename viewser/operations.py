"""
High-level operations intended for users
"""
import logging
import time
from requests import HTTPError
from . import models,crud,settings
logger = logging.getLogger(__name__)

def publish(queryset:models.Queryset):
    """
    Publishes a queryset to the ViEWSER databases, which can then be fetched
    by calling `viewser.operations.fetch(queryset.name)`
    """

    try:
        crud.post_queryset(queryset)
    except HTTPError as httpe:
        logger.info("Queryset named \"%s\" exists, updating",
                queryset.name
            )
    else:
        return

    try:
        crud.update_queryset(queryset)
    except HTTPError as httpe:
        logger.critical("Update returned %s: %s",
                str(httpe.response.status_code),
                str(httpe.response.content),
            )

def fetch(queryset_name:str):
    """
    Fetches data for a queryset, 
    """
    retries = 0
    while retries < settings.config("RETRIES"):
        try:
            return crud.fetch_queryset(queryset_name)
        except crud.OperationPending:
            logger.info("Queryset \"%s\" is being compiled... (%s retries)",
                    queryset_name, str(retries)
                    )
            retries += 1
            time.sleep(settings.config("RETRY_FREQUENCY"))
