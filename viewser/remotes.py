from collections import namedtuple
from typing import Dict, Optional, Any, List, Callable
import json
import os
import webbrowser
import logging
from urllib import parse
import toml
import requests
from requests import Response
import pydantic
from pymonad.either import Left, Right, Either
from pymonad.maybe import Nothing, Maybe
from toolz.functoolz import curry, compose

from . import exceptions, schema

logger = logging.getLogger(__name__)


ExceptionOrResponse = Either[Exception,Response]

def pydantic_validate(val, type):
    class mdl(pydantic.BaseModel):
        x: type
    return mdl(x=val).x

def make_request(
        url: str,
        method: str = "GET",
        json_data: Maybe[Dict[str,Any]] = Nothing) -> ExceptionOrResponse:
    """
    make request

    Make a request to url, with optional data.

    Args:
        url(str): The url to request
        method(str): The method to use

        json_data(Maybe[Dict[str,Any]]): Optional JSON data to pass with request

    Returns:
        Either[Exception, Response]
    """
    request_args = [method, url]
    request_kwargs = {"headers":{}}

    def update_kwargs(kwargs, data):
        kwargs.update({"data":data})
        kwargs["headers"].update({"Content-Type":"application/json"})
        return kwargs

    request_kwargs = (json_data
        .then(json.dumps)
        .maybe(request_kwargs, curry(update_kwargs, request_kwargs))
        )

    try:
        response = requests.request(*request_args,**request_kwargs)
    except requests.RequestException as re:
        return Left(re)

    return Right(response)

def response_check(
        check_fn: Callable[[Response],bool],
        exc_fn: Callable[[Response], Exception],
        response: Response) -> ExceptionOrResponse:
    """
    response_check

    Returns a function that can be used to check a
    response. The resulting check function returns
    either a Left containing an exception, or a Right
    containing the response.

    Args:
        check_fn: A callable that takes a response, and returns a bool
        exc_fn: A callable that takes a response, and returns an exception
        response: Response

    Returns:
        Either[Exception, Response]
    """
    if not check_fn(response):
        return Left(exc_fn(response))
    else:
        return Right(response)

ResponseCheck = Callable[[ExceptionOrResponse], ExceptionOrResponse]

def check_pending(response: Response) -> ExceptionOrResponse:
    """
    check_pending

    Checks whether a response returned a status 202, which signifies that the
    requested result is still pending.
    """
    logger.debug(f"Checking if {response.url} is pending")
    return response_check(
            lambda rsp: rsp.status_code != 202,
            OperationPending,
            response
        )

def check_error(response: Response) -> ExceptionOrResponse:
    """
    check_error

    Checks whether a response returned a status 5xx, which signifies that the
    request resulted in an error on the remote server.
    """
    logger.debug(f"Checking if {response.url} resulted in an error")
    return response_check(
            lambda rsp: str(rsp.status_code)[0] != "5", exceptions.RemoteError,
            response
        )

def check_content_type(content_type: str, response: Response) -> ExceptionOrResponse:
    """
    check_content_type

    Check whether a response returned the correct content type.
    """
    logger.debug(f"Checking if {response.url} had the correct Content-Type ({content_type})")
    get_content_type = lambda rsp: rsp.headers["Content-Type"]

    try:
        return response_check(
                lambda rsp: get_content_type(rsp) == content_type,
                lambda _: TypeError(f"""
                    {response.url} had wrong content type.
                    Expected: {content_type}
                    Got: {get_content_type(response)}
                    """),
                response
                )
    except KeyError:
        return Left(TypeError(f"""
            {response.url} had no content type in header.
            Expected: {content_type}
        """))

def check_404(response: Response) -> ExceptionOrResponse:
    """
    check_404

    Checks whether a 4xx error occurred while making the request.
    """
    return response_check(
            lambda rsp: rsp.status_code != 404,
            exceptions.NotFoundError,
            response,
            )

def check_4xx(response: Response) -> ExceptionOrResponse:
    """
    check_4xx

    Checks whether a 4xx error occurred while making the request.
    """
    return response_check(
            lambda rsp: str(rsp.status_code)[0] != "4",
            exceptions.ClientError,
            response,
            )

status_checks = [
        check_4xx,
        check_pending,
        check_404,
        check_error,
    ]

def make_url(base_url: str, path: str, parameters = Nothing)-> Either[Exception, str]:
    """
    make_url

    Make an url, by combining a base url, a path, and an
    optional dictionary of parameters.

    Args:
        base_url(str): Protocol and host, ex http://foo.com
        path(str): Path to add to the base, ex. /foo/bar
        parameters(Maybe[Dict[str,str]]): Optional dict of parameters

    Returns:
        str
    """
    try:
        raw = base_url.strip("/") + "/" + path

        url = pydantic_validate(raw, pydantic.HttpUrl)

        with_pstring = (parameters
            .then(parse.urlencode)
            .maybe(url, lambda x: url + "?" + x)
            )
        return Right(with_pstring)

    except pydantic.ValidationError as ve:
        return Left(ve)

def compose_checks(
        checks: List[ResponseCheck]
        )-> Callable[[ExceptionOrResponse],ExceptionOrResponse]:
    make_then = lambda fn: lambda x: x.then(fn)
    return compose(*[make_then(fn) for fn in checks])

def request(
        base_url: str,
        method: str,
        checks: List[ResponseCheck],
        path: str,
        parameters: Maybe[Dict[str,str]] = Nothing,
        data: Maybe[Dict[str,Any]] = Nothing
        ) -> ExceptionOrResponse:
    """
    request

    Make a request, returning either a Right(response) or a Left(exception).

    Args:
        base_url(str): The base url
        method(str): The method to use (GET, POST, etc)
        checks(ResponseCheck): A list of checks (see response_check)

        path(str): The path to request

        parameters(Maybe[Dict[str,str]]): An optional dict of query-string parameters
        data(Maybe[Dict[str,Any]]): An optional JSON dict to send to the server

    Returns:
        Either[Response, Exception]
    """
    url = make_url(base_url, path, parameters)
    response = url.then(curry(make_request, method = method, json_data = data))
    return compose_checks(checks)(response)

class Api:
    def __init__(self,
            base_url: str,
            paths: Dict[str,schema.IRemotePaths]):
        self._base_url = base_url
        self.paths = paths
        logger.warning("The remotes.Api class is deprecated")

    def url(self,*args,**kwargs):
        url = os.path.join(self._base_url,*args)

        kwargs = {k:v for k,v in kwargs.items() if v is not None}
        if kwargs:
            url += "?" + parse.urlencode(kwargs)
        return url

    @staticmethod
    def check_response(response):
        if response.status_code == 202:
            raise exceptions.OperationPending

        if str(response.status_code)[0] == "2":
            pass
        else:
            raise requests.HTTPError(response = response)

    def remote(self,
            base: schema.IRemotePaths,
            path: str = "",
            method = "GET",
            parameters: Optional[Dict[str,str]] = {},
            **kwargs):

        path = os.path.join(self.paths[base],path)
        return self._http(method, (path,), parameters, **kwargs)

    def _http(self,method,path,parameters,*args,**kwargs):
        url = self.url(*path,**parameters)
        logger.debug("Requesting url %s",url)
        try:
            rsp = requests.request(method,url,*args,**kwargs)
        except requests.exceptions.MissingSchema:
            raise exceptions.ConfigurationError(
                    f"Bad URL provided: \"{url}\"",
                    hint = "Did you configure viewser correctly? "
                        "Try running `viewser config list` to see your configuration"
                )
        self.check_response(rsp)
        return rsp

def browser(base,*args,**kwargs):
    webbrowser.open(Api(base,{}).url(*args,**kwargs))

def latest_pyproject_version(repo_url):
    """
    Gets the latest version of the CLI from Github
    """
    repo_path = parse.urlparse(repo_url).path
    url = parse.urljoin("https://raw.githubusercontent.com/",repo_path)
    url = os.path.join(url,"master/pyproject.toml")

    rsp = requests.get(url)
    Api.check_response(rsp)
    pyproject = toml.loads(rsp.content.decode())
    version = pyproject["tool"]["poetry"]["version"]
    logger.debug("Latest version from github: %s",version)
    return version

