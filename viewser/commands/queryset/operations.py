"""
queryset_operations
===================

"""
import time
from typing import Optional, List
from io import BytesIO, BufferedWriter
from datetime import date
import logging
import pydantic
from pyarrow.lib import ArrowInvalid
import pandas as pd
import requests
from toolz.functoolz import do, curry
from pymonad.either import Either, Left, Right
from pymonad.maybe import Just, Nothing, Maybe
from views_schema import viewser as viewser_schema
from views_schema import queryset_manager as queryset_schema
from viewser import settings, remotes
from viewser.error_handling import errors, error_handling
from viewser.tui import animations

from . import queryset_list

logger = logging.getLogger(__name__)

REMOTE_URL = settings.config_get("REMOTE_URL")
REPO_URL = settings.config_get("REPO_URL")

response_json = lambda rsp: rsp.json()

class QuerysetOperations():

    def __init__(self, remote_url: str, error_handler: Optional[error_handling.ErrorDumper] = None):
        self._error_handler = error_handler if error_handler else error_handling.ErrorDumper([])
        self._remote_url = remote_url

    def fetch(self, queryset_name:str, out_file: Optional[BufferedWriter] = None, start_date: Optional[date] = None, end_date: Optional[date] = None) -> None:
        """
        fetch
        =====

        parameters:
            queryset_name (str): Name of the queryset to fetch
            out_file (BufferedWriter): File to write queryset to

        returns:
            None: Always returns none. Errors are handled and reported internally if they occur.

        """
        f = self._fetch(
                settings.config_get("RETRIES"),
                REMOTE_URL,
                queryset_name,
                start_date, end_date)
        if out_file is not None:
            f.then(curry(do, lambda data: data.to_parquet(out_file)))

        return f.either(self._error_handler.dump, Just)

    def list(self) -> Maybe[queryset_list.QuerysetList]:
        """
        list
        ====

        returns:
            Optional[List[str]]: Returns a list of queryset name if operation succeeds.

        """
        return (self._request("GET", remotes.status_checks, "querysets")
            .then(lambda r: r.json())
            .then(lambda d: queryset_list.QuerysetList(**d))
            .either(self._error_handler.dump, Just))

    def show(self, name: str) -> Maybe[queryset_schema.DetailQueryset]:
        """
        show
        ====

        parameters:
            name (str): Name of the queryset to show

        returns:
            Optional[viewser_schema.queryset_manager.DetailQueryset]: Returns queryset model if successful.
        """
        return (self._request("GET", remotes.status_checks, f"querysets/{name}")
            .then(lambda r: r.json())
            .then(lambda d: queryset_schema.DetailQueryset(**d))
            .either(self._error_handler.dump, Just))

    def publish(self, queryset: queryset_schema.Queryset, overwrite: bool = True) -> Maybe[requests.Response]:
        (self._request(
                "POST",
                remotes.status_checks,
                "querysets",
                parameters = Just({"overwrite":overwrite}),
                data = Just(queryset.dict()))
            .either(self._error_handler.dump, Just))

    def delete(self, name: str) -> Maybe[requests.Response]:
        (self._request( "DELETE",
                remotes.status_checks,
                f"querysets/{name}",
                )
            .either(self._error_handler.dump, Just))

    def _request(self, method: str, checks, path, **kwargs) -> Either[viewser_schema.Dump, requests.Response]:
        return remotes.request(self._remote_url, method, checks, path, **kwargs)

    def _deserialize(self, response: requests.Response) -> Either[viewser_schema.Dump, pd.DataFrame]:
        if response.status_code == 202:
            # No data yet
            return Right(None)
        else:
            try:
                return Right(pd.read_parquet(BytesIO(response.content)))
            except (OSError, ArrowInvalid):
                return Left(errors.deserialization_error(response))

    def _fetch(
            self,
            max_retries : int,
            base_url: str, name: str,
            start_date: Optional[date] = None, end_date: Optional[date] = None
            ) -> Either[viewser_schema.Dump, pd.DataFrame]:
        """
        _fetch
        ======

        Fetches queryset located at {base_url}/querysets/data/{name}

        Args:
            base_url(str)
            name(str)
            start_date(Optional[str]): Only fetch data after start_date
            start_date(Optional[str]): Only fetch data before end_date

        Returns:
            Either[errors.Dump, pd.DataFrame]

        """
        start_date, end_date = [date.strftime("%Y-%m-%d") if date else None for date in (start_date, end_date)]

        checks = [
                    remotes.check_4xx,
                    remotes.check_error,
                    remotes.check_404,
                 ]

        parameters = {
                k:v for k,v in {"start_date":start_date, "end_date":end_date}.items() if v is not None
                }
        parameters = Just(parameters) if len(parameters) > 0 else Nothing
        path = f"querysets/data/{name}"

        retries = 0
        anim    = animations.LineAnimation()
        data    = Right(None)

        while (data.is_right() and data.value is None):
            if retries > 0:
                time.sleep(1)

            anim.print_next()

            data = (remotes.request(base_url, "GET", checks, path, parameters = parameters)
                .then(self._deserialize))

            if retries > max_retries:
                data = Left(errors.max_retries())

            retries += 1

        anim.end()

        return data

def fetch(queryset_name: str, start_date: Optional[date] = None, end_date: Optional[date] = None) -> pd.DataFrame:
    """
    fetch
    =====

    parameters:
        queryset_name (str)

    returns:
        pandas.DataFrame

    Fetch a queryset
    """
    return QuerysetOperations(
            settings.REMOTE_URL,
            error_handling.ErrorDumper([error_handling.StreamHandler()])
            ).fetch(queryset_name).maybe(None, lambda x:x)
