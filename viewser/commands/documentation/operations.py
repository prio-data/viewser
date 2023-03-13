
import os
import logging

from views_schema import docs as schema
from views_schema.viewser import Dump
from pymonad.either import Either, Left, Right
from pymonad.maybe import Just
from pydantic import ValidationError
from requests.exceptions import JSONDecodeError

from viewser import remotes
from viewser.error_handling import errors

logger = logging.getLogger(__name__)

class DocumentationCrudOperations():
    """
    DocumentationCrudOperations
    ===========================

    parameters:
        base_url (str)
        path (str)

    Class for doing CRUD on documentation for views3
    """


    def __init__(self, base_url: str, path: str):
        self._base_url = os.path.join(base_url, path)

    def post(self, posted: schema.PostedDocumentationPage, name: str = None, overwrite: bool = False)-> Either[Dump, schema.ViewsDoc]:

        if name is None:
            name = posted.name

        if not overwrite:
            try:
                assert not self._exists(name)
            except AssertionError:
                return Left(errors.exists_error(name))

        return (remotes.request(self._base_url,"POST", remotes.status_checks, name, data = Just(posted.dict()))
            .then(lambda _: remotes.request(self._base_url, "GET", remotes.status_checks, name))
            .then(self._deserialize))

    def list(self) -> Either[Dump, schema.ViewsDoc]:
        return self.show("")

    def show(self, name: str) -> Either[Dump, schema.ViewsDoc]:
        return remotes.request(self._base_url, "GET", remotes.status_checks, name).value.content.decode()#.then(self._deserialize)


    def _exists(self,name: str) -> Either[Dump, bool]:
        response = remotes.request(self._base_url, "GET", [], name)
        return response.is_right() and response.value.status_code == 200

    def _deserialize(self, response) -> Either[Dump, schema.ViewsDoc]:
        try:
            return Right(schema.ViewsDoc(**response.json()))
        except (JSONDecodeError, ValidationError):
            return Left(errors.deserialization_error(response))
