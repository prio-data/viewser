from typing import Optional
import logging
from io import BytesIO
import pandas as pd
import views_schema
from . import remotes

logger = logging.getLogger(__name__)

def check_parquet_response(response):
    if response.headers.get("Content-Type") == "application/octet-stream":
        pass
    else:
        raise remotes.RemoteError(
                f"Remote {response.url} returned wrong content type: "
                f"{response.headers.get('Content-Type')}"
                )

def fetch_queryset(
        remotes_api: remotes.Api,
        name,
        start_date:Optional[str]=None,
        end_date:Optional[str]=None):

    response = remotes_api.http(
            "GET",
            ("data",name),
            {"start_date":start_date,"end_date": end_date}
            )

    check_parquet_response(response)
    return pd.read_parquet(BytesIO(response.content))

def post_queryset(
        remotes_api: remotes.Api,
        queryset: views_schema.Queryset,
        overwrite: bool = True):
    """
    Post a queryset to the remote API
    """
    return remotes_api.http("POST",
            ("queryset",), {"overwrite":overwrite},
            data=queryset.json()).json()

def put_queryset(remotes_api: remotes.Api, name:str,queryset: views_schema.Queryset):
    """
    Put a queryset to the remote API, overwriting the existing queryset
    """
    queryset.name = None
    return remotes_api.http("PUT",("queryset",name),{},data=queryset.json()).json()

update_queryset = lambda remotes_api, queryset: put_queryset(remotes_api, queryset.name, queryset)

def list_querysets(remotes_api: remotes.Api):
    """
    List available querysets
    """
    return remotes_api.http("GET",("queryset",),{}).json()

def delete_queryset(remotes_api: remotes.Api, name):
    """
    Delete a named queryset
    """
    return remotes_api.http("DELETE",("queryset",name),{})

def show_queryset(remotes_api: remotes.Api, name:str):
    """
    Show details about a queryset
    """
    return remotes_api.http("GET",("queryset",name),{}).json()
