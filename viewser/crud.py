from abc import ABC, abstractmethod
from typing import Optional, Generic, TypeVar, Dict, List
import functools
import logging
import requests

import views_schema
from . import exceptions

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
            raise exceptions.RequestError(response = response) from ae
        return response

    def _check_post_exists(self,name: str)-> bool:
        try:
            self.show(name)
        except exceptions.RequestError as re:
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
