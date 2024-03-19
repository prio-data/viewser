"""
queryset_operations
===================

"""
import sys
import time
from typing import Optional
from io import BytesIO, BufferedWriter
from datetime import date
import logging
from pyarrow.lib import ArrowInvalid
import pandas as pd
import io
import requests
from pymonad.either import Either, Left, Right
from pymonad.maybe import Just, Nothing, Maybe
from views_schema import viewser as viewser_schema
from views_schema import queryset_manager as queryset_schema
from viewser import remotes
from viewser.error_handling import errors, error_handling
from . import drift_detection

from IPython.display import clear_output

from . import queryset_list

logger = logging.getLogger(__name__)

response_json = lambda rsp: rsp.json()


class QuerysetOperations():

    def __init__(self,
            remote_url: str,
            error_handler: Optional[error_handling.ErrorDumper] = None,
            max_retries: int = sys.maxsize):
        self._remote_url = remote_url
        self._max_retries = max_retries
        self._error_handler = error_handler if error_handler else error_handling.ErrorDumper([])

    def fetch(self, queryset_name: str,
              out_file: Optional[BufferedWriter] = None,
              start_date: Optional[date] = None,
              end_date: Optional[date] = None) -> pd.DataFrame:
        """
        fetch
        =====

        parameters:
            queryset_name (str): Name of the queryset to fetch
            out_file (BufferedWriter): File to write queryset to

        returns:
            Maybe[pandas.DataFrame]: Dataframe corresponding to queryset (if query succeeds)

        """

        f = self._fetch(
            self._max_retries,
            self._remote_url,
            queryset_name,
            start_date, end_date)

        return f

    def fetch_with_drift_detection(self,
                                   queryset_name: str,
                                   out_file: Optional[BufferedWriter] = None,
                                   start_date: Optional[date] = None,
                                   end_date: Optional[date] = None,
                                   drift_config_dict: Optional[dict] = None
                                   ):

        df = self.fetch(queryset_name, out_file=out_file, start_date=start_date, end_date=end_date)

        input_alerts = drift_detection.InputGate(df, drift_config_dict).assemble_alerts()

        return df, input_alerts

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
            ) -> pd.DataFrame:
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
#        start_date, end_date = [date.strftime("%Y-%m-%d") if date else None for date in (start_date, end_date)]

        checks = [
                    remotes.check_4xx,
                    remotes.check_error,
                    remotes.check_404,
                 ]

        parameters = {
                k:v for k,v in {"start_date":start_date, "end_date":end_date}.items() if v is not None
                }
        parameters = Just(parameters) if len(parameters) > 0 else Nothing
        path = f"data/{name}"

        retries = 0

        data    = None
        message = None

        failed = False
        succeeded = False

        while not (succeeded or failed):
            if retries > 0:
                time.sleep(5)

            data = remotes.request(base_url, "GET", checks, path, parameters=parameters)

            try:
                data = pd.read_parquet(io.BytesIO(data.value.content)).loc[start_date:end_date]
                data.index = data.index.remove_unused_levels()
                print(f'\n')
                print(f'Queryset {name} read successfully')

                succeeded = True
            except:
                message = data.value.content.decode()
                if retries == 0:
                    print(f'\n')
                    print(f'\r {retries + 1}: {message}', flush=True, end="\r")
                else:
                    print(f'\r {retries + 1}: {message}', flush=True, end="\r")
                if 'failed' in message:
                    failed = True
                    data = message

            if retries > max_retries:
                print(f'\n')
                print(f'Max attempts to retrieve exceeded ({max_retries}) : aborting retrieval', end="\r")
                failed = True
                data = message

            retries += 1

        return data