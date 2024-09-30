"""
queryset_operations
===================

"""
import sys
import time
from typing import Optional, Dict
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
from . import drift_detection

logger = logging.getLogger(__name__)


class QuerysetOperations():

    def __init__(self,
                 remote_url: str,
                 error_handler: Optional[error_handling.ErrorDumper] = None,
                 max_retries: int = sys.maxsize):

        self._remote_url = remote_url
        self._max_retries = max_retries
        self._error_handler = error_handler if error_handler else error_handling.ErrorDumper([])

    def fetch(self, queryset_name: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        fetch
        =====

        parameters:
            queryset_name (str): Name of the queryset to fetch
            out_file (BufferedWriter): File to write queryset to

        returns:
            Maybe[pandas.DataFrame]: Dataframe corresponding to queryset (if query succeeds)

        """

        if bool(start_date) != bool(end_date):
            raise RuntimeError(f'You must specify either both or neither of start_date and end_date')

        if start_date is not None:
            try:
                start_date = int(start_date)
                end_date = int(end_date)
            except:
                raise RuntimeError(f'Unable to cast start and/or end date values {start_date, end_date} to integer')

            if start_date < 1 or end_date < 1:
                raise RuntimeError(f'Start and/or end date values {start_date, end_date} less than 1')

            if start_date > end_date:
                raise RuntimeError(f'Start date {start_date} bigger than end date {end_date}')

        f = self._fetch(
            self._max_retries,
            self._remote_url,
            queryset_name,
            start_date,
            end_date
            )

        return f

    def fetch_with_drift_detection(self, queryset_name: str, start_date: str, end_date: str, drift_config_dict:
                                   Optional[Dict] = None, self_test: Optional[bool] = False):
        """
        fetch_with_drift_detection
        =====

        parameters:
            queryset_name (str): Name of the queryset to fetch
            start_date: first month to include in output
            end_data: last month to include in output
            drift_config_dict: dictionary specifying which drift detection parameters to use

        returns:
            Dataframe corresponding to queryset (if query succeeds)

        """

        self_test_data = None

        if self_test:
            try:
                self_test_data = self.fetch("drift_detection_self_test", start_date, end_date)
            except:
                print(f'Attempt to fetch elf test qs failed. Self test queryset MUST be defined outside viewser')
                raise RuntimeError

        f = self.fetch(queryset_name, start_date, end_date)

        input_gate = drift_detection.InputGate(f, drift_config_dict=drift_config_dict, self_test=self_test,
                                               self_test_data=self_test_data)

        alerts = input_gate.assemble_alerts()

        return f, alerts

    def list(self):
        """
        list
        ====

        returns:
            Returns a list of queryset names if operation succeeds.

        """

        response = requests.request(method="GET", url=f'{self._remote_url}/querysets')

        return response.json()['querysets']

    def qs_json_to_code(self, json_):

        allowed_fields = ['name', 'loa', 'description', 'themes', 'operations']
        allowed_namespaces = ['base', 'trf']

        for key in json_.keys():
            if key not in allowed_fields:
                raise RuntimeError(f'Queryset json contains unrecognised field: {key}')

        lines = []

        tab = '    '

        line = f"(Queryset('{json_['name']}','{json_['loa']}')"

        lines.append(line)

        ops = json_['operations']

        for column in ops:
            for op in column[::-1]:
                if op['namespace'] not in allowed_namespaces:
                    raise RuntimeError(f"Queryset operation contains unrecognised namespace: {op['namespace']}")
                if op['namespace'] == 'base':
                    for op2 in column:
                        if op2['namespace'] == 'trf' and op2['name'] == 'util.rename': rename = op2['arguments'][0]
                    loa, name = op['name'].split('.')

                    line = f"{tab}.with_column(Column('{rename}', from_loa='{loa}', from_column='{name}')"
                    lines.append(line)
                    if op['arguments'][0] != 'values':
                        arg = op['arguments'][0]
                        line = f"{tab}{tab}.aggregate('{arg}')"
                        lines.append(line)

                if op['namespace'] == 'trf' and op['name'] != 'util.rename':
                    args = ','.join(op['arguments'])
                    line = f"{tab}{tab}.transform.{op['name']}({args})"
                    lines.append(line)

            line = f"{tab}{tab})"
            lines.append(line)
            line = f""
            lines.append(line)

        if len(json_['themes']) > 0:
            line = f"{tab}.with_theme('{json_['themes'][0]}')"
            lines.append(line)

        if json_['description'] is not None:
            line = f'{tab}.describe("""{json_["description"]}""")'
            lines.append(line)

        line = f"{tab})"
        lines.append(line)

        qs_code = '\n'.join(lines)

        return qs_code

    def show(self, queryset: str):
        """
        show
        ====

        returns:
            Returns code representing a queryset.

        """

        response = requests.request(method="GET", url=f'{self._remote_url}/querysets/{queryset}')

        json_ = response.json()

        return self.qs_json_to_code(json_)

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

        url = self._remote_url + f"/querysets/{name}"

        response = requests.request(method=method, url=url)

        return response

    def _fetch(self, max_retries: int, base_url: str, name: str, start_date: int, end_date: int) -> pd.DataFrame:
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

        if start_date is not None:
            path = f"data/{name}?" + parse.urlencode({"start_date": start_date, "end_date": end_date})
            url = self._remote_url + '/' + path
        else:
            path = f"data/{name}"
            url = self._remote_url + '/' + path

        retries = 0
        delay = 5

        failed = False
        succeeded = False
        block_size = 1024

        last_line_length = 0

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
                    data = pd.DataFrame()

            if retries > max_retries:

                clear_output(wait=True)
                print(f'Max attempts ({max_retries}) to retrieve {name} exceeded: aborting retrieval', end="\r")

                failed = True
                data = pd.DataFrame()

            retries += 1
            time.sleep(delay)

        return data
