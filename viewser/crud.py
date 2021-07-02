from abc import ABC, abstractmethod
from typing import Optional, Generic, TypeVar, Dict, List
import functools
import logging
from io import BytesIO
import pandas as pd
import requests
import views_schema
from . import remotes, schema, exceptions

logger = logging.getLogger(__name__)

PostedModel = TypeVar("PostedModel")
ListedModel = TypeVar("ListedModel")
DetailModel = TypeVar("DetailModel")

class CrudOperations(ABC, Generic[PostedModel, ListedModel, DetailModel]):

    @property
    @abstractmethod
    def __posted_model__(self)-> Dict[str,str]:
        pass

    @property
    @abstractmethod
    def __listed_model__(self)-> Dict[str,str]:
        pass

    @property
    @abstractmethod
    def __detail_model__(self)-> Dict[str,str]:
        pass

    @property
    @abstractmethod
    def __locations__(self)-> Dict[str,str]:
        pass

    def __init__(self, base_url: str):
        self._base_url = base_url

    def _url(self, path: Optional[str] = None, location: str = "main")-> str:
        url = self._base_url + "/" + self.__locations__[location]
        if path:
            url = url + "/" + path
        return url

    @functools.wraps(requests.request)
    def _http(self,*args,**kwargs)-> requests.Request:
        response = requests.request(*args,**kwargs)
        try:
            assert str(response.status_code)[0] == "2"
        except AssertionError as ae:
            raise exceptions.RemoteError(response = response) from ae
        return response

    def _check_post_exists(self,name: str)-> bool:
        try:
            self.show(name)
        except exceptions.RemoteError as re:
            if re.response.status_code == 404:
                return False
            else:
                raise re
        else:
            return True

    def post(self, posted: PostedModel, name: str = None, overwrite: bool = False)-> DetailModel:

        if name is None:
            name = posted.name

        if not overwrite:
            try:
                assert not self._check_post_exists(name)
            except AssertionError:
                raise exceptions.ExistsError

        self._http("POST", self._url(name),
                data = posted.json(),
                headers = {"Content-Type":"application/json"}
                )

        now_exists = self._http("GET", self._url(name))
        return self.__detail_model__(**now_exists.json())

    def list(self) -> List[ListedModel]:
        listed = self._http("GET", self._url())
        return [self.__listed_model__(**mdl) for mdl in listed.json()]

    def show(self, name: str) -> DetailModel:
        detail = self._http("GET", self._url(name))
        return self.__detail_model__(**detail.json())

class QuerysetCrudOperations(CrudOperations[
    views_schema.PostedQueryset,
    views_schema.ListedQueryset,
    views_schema.DetailQueryset]):
    __posted_model__ = views_schema.PostedQueryset
    __listed_model__ = views_schema.ListedQueryset
    __detail_model__ = views_schema.DetailQueryset

    __locations__ = {
            "main": "querysets/querysets",
            "fetch": "querysets/data"
        }

    def fetch(self, name: str)-> pd.DataFrame:
        data = self._http(self._url(name, location = "fetch"))
        data_buffer = BytesIO(data.content)
        return pd.read_parquet(data_buffer)

class DocumentationCrudOperations(CrudOperations[
    views_schema.PostedDocumentationPage,
    views_schema.ViewsDoc,
    views_schema.ViewsDoc]):

    @property
    def __locations__(self):
        return {
            "main": f"docs/{self.path}"
        }

    @property
    def __listed_model__(self):
        raise AttributeError("DocumentationCrud does not have a listed_model")

    def __init__(self, base_url: str, path: str):
        self.path = path
        super().__init__(base_url)

    __posted_model__ = views_schema.PostedDocumentationPage
    __detail_model__ = views_schema.ViewsDoc

    def _check_post_exists(self,name: str)->bool:
        doc_page = self.show(name)
        if doc_page.page is None:
            return False
        else:
            return True

    def list(self) -> views_schema.ViewsDoc:
        return self.show("")

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

    response = remotes_api.remote(
            schema.IRemotePaths.querysets,
            path = "data/"+name,
            parameters = {"start_date":start_date,"end_date": end_date}
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
    return remotes_api.remote(
            schema.IRemotePaths.querysets,
            "querysets",
            method = "POST",
            parameters={"overwrite":overwrite},
            data=queryset.json(),
            headers={"Content-Type":"application/json"}).json()

def put_queryset(remotes_api: remotes.Api, name:str,queryset: views_schema.Queryset):
    """
    Put a queryset to the remote API, overwriting the existing queryset
    """
    queryset.name = None
    return remotes_api.remote(
            schema.IRemotePaths.querysets,
            "querysets/" + name,
            method = "PUT",
            data=queryset.json()
            ).json()

update_queryset = lambda remotes_api, queryset: put_queryset(remotes_api, queryset.name, queryset)

def list_querysets(remotes_api: remotes.Api):
    """
    List available querysets
    """
    return remotes_api.remote(schema.IRemotePaths.querysets,"querysets").json()

def delete_queryset(remotes_api: remotes.Api, name):
    """
    Delete a named queryset
    """
    return remotes_api.remote(
            schema.IRemotePaths.querysets,
            "querysets/"+name,
            method = "DELETE")

def show_queryset(remotes_api: remotes.Api, name:str):
    """
    Show details about a queryset
    """
    return remotes_api.remote(
            schema.IRemotePaths.querysets,
            "querysets/"+name).json()
