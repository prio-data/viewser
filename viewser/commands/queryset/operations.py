"""
queryset_operations
===================

"""
import sys
import time
from typing import Optional
from urllib import parse
from tqdm import tqdm
import json
import logging
import pandas as pd
import io
import requests
from views_schema import queryset_manager as queryset_schema
from viewser.error_handling import error_handling

from IPython.display import clear_output

from . import queryset_list

logger = logging.getLogger(__name__)


class QuerysetOperations():

    def __init__(self,
                 remote_url: str,
                 error_handler: Optional[error_handling.ErrorDumper] = None,
                 max_retries: int = sys.maxsize):

        self._remote_url = remote_url
        self._max_retries = max_retries
        self._error_handler = error_handler if error_handler else error_handling.ErrorDumper([])

    def fetch(self, queryset_name: str) -> pd.DataFrame:
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
            )

        return f

    def list(self) -> queryset_list.QuerysetList:
        """
        list
        ====

        returns:
            Optional[List[str]]: Returns a list of queryset name if operation succeeds.

        """

        response = requests.request(method="GET", url=f'{self._remote_url}/querysets')

        qs_list = queryset_list.QuerysetList()

        qs_list.querysets = response.content

        return qs_list

    def publish(self, queryset: queryset_schema.Queryset, overwrite: bool = True) -> requests.Response:

        method = "POST"

        url = self._remote_url + "/querysets?" + parse.urlencode({"overwrite": overwrite})

        request_kwargs = {"headers": {}}

        request_kwargs.update({"data": json.dumps(queryset.dict())})

        request_kwargs["headers"].update({"Content-Type": "application/json"})

        response = requests.request(method=method, url=url, **request_kwargs)

        return response

    def delete(self, name: str) -> requests.Response:

        method = "DELETE"

        url = self._remote_url + f"/querysets{name}"

        response = requests.request(method=method, url=url)

        return response

    def _fetch(self, max_retries: int, base_url: str, name: str) -> pd.DataFrame:
        """
        _fetch
        ======
        Fetches queryset located at {base_url}/querysets/data/{name}
        Args:
            base_url(str)
            name(str)
        Returns:
            pd.DataFrame
        """

        def overprint(message_string, last_line_length, end):
            space = ' '
            new_line_length = len(message_string)
            pad = max(0, last_line_length - new_line_length)
            print(f'{message_string}{(pad + 1) * space}', end=end)

            return new_line_length

        path = f"data/{name}"

        empty_df = pd.DataFrame()
        retries = 0
        delay = 5

        failed = False
        succeeded = False
        block_size = 1024

        last_line_length = 0

        url = base_url + '/' + path + '/'

        while not (succeeded or failed):

            data = io.BytesIO()

            response = requests.get(url, stream=True)
            total_size = int(response.headers.get("content-length", 0))

            if total_size > 1e6:
                with tqdm(total=total_size, unit="B", unit_scale=True) as progress_bar:
                    for segment in response.iter_content(block_size):
                        progress_bar.update(len(segment))
                        data.write(segment)

            else:
                for segment in response.iter_content(block_size):
                    data.write(segment)

            try:
                data = pd.read_parquet(data)

                message_string = f'Queryset {name} read successfully'
                new_line_length = overprint(message_string, last_line_length, end="\n")

                succeeded = True

            except:
                message = data.getvalue().decode()
                message_string = f'{retries + 1}: {message}'
                last_line_length = overprint(message_string, last_line_length, end="\r")

                if 'failed' in message:
                    failed = True
                    data = empty_df

            if retries > max_retries:

                clear_output(wait=True)
                print(f'Max attempts ({max_retries}) to retrieve {name} exceeded: aborting retrieval', end="\r")

                failed = True
                data = empty_df

            retries += 1
            time.sleep(delay)

        return data
