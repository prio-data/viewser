import os
from typing import Optional
import logging
from io import BytesIO
from urllib.parse import urlencode
import requests
import pandas as pd
from . import settings,models

logger = logging.getLogger(__name__)

remote_url = lambda path: os.path.join(settings.config("REMOTE_URL"),path)

class OperationPending(Exception):
    pass

class RemoteError(Exception):
    pass

def check_response(response):
    if response.status_code == 200:
        pass
    elif response.status_code == 202:
        raise OperationPending
    else:
        raise requests.HTTPError(response=response)

def check_parquet_response(response):
    check_response(response)
    if response.headers.get("Content-Type") == "application/octet-stream":
        pass
    else:
        raise RemoteError(
                f"Remote {response.url} returned wrong content type: "
                f"{response.headers.get('Content-Type')}"
                )

def fetch_queryset(name,start_date:Optional[str]=None,end_date:Optional[str]=None):
    url = remote_url(os.path.join("data",name))

    query_parameters = {"start_date":start_date,"end_date":end_date}
    query_parameters = {q:p for q,p in query_parameters.items() if p is not None}
    url += "?"+urlencode(query_parameters)

    logging.debug("Requesting %s",url)
    response = requests.get(url)
    check_parquet_response(response)
    return pd.read_parquet(BytesIO(response.content))

def post_queryset(queryset: models.Queryset):
    url = remote_url("queryset")
    response = requests.post(url,data=queryset.json())
    if str(response.status_code)[0] != "2":
        raise requests.HTTPError(response=response)

def put_queryset(name:str,queryset:models.Queryset):
    url = remote_url(os.path.join("queryset",name))
    response = requests.put(url,data=queryset.json())
    if str(response.status_code)[0] != "2":
        raise requests.HTTPError(response=response)

update_queryset = lambda queryset: put_queryset(queryset.name,queryset)

def list_querysets():
    url = remote_url("queryset")
    response = requests.get(url)
    if response.status_code != 200:
        raise requests.HTTPError(response=response)
    return response.content.decode()

def delete_queryset(name):
    url = remote_url(os.path.join("queryset",name))
    response = requests.delete(url)
    if str(response.status_code)[0] != "2":
        raise requests.HTTPError(response=response)
    return response.content.decode()

def show_queryset(name:str):
    url = remote_url(os.path.join("queryset",name))
    response = requests.get(url)
    if response.status_code != 200:
        raise requests.HTTPError(response=response)
    return response.content.decode()


if __name__ == "__main__":
    fetch_queryset("test_set_quick")
