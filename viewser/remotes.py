from typing import Dict, Any, List, Callable
import json
import logging
from urllib import parse
import requests
from requests import Response
import pydantic
from pymonad.either import Left, Right, Either
from pymonad.maybe import Nothing, Maybe
from toolz.functoolz import curry, compose
from views_schema import viewser as schema

from .error_handling import errors

logger = logging.getLogger(__name__)

def make_request(
        url: str,
        method: str = "GET",
        json_data: Maybe[Dict[str,Any]] = Nothing) -> Either[schema.Dump, Response]:
    """
    make request

    Make a request to url, with optional data.

    Args:
        url(str): The url to request
        method(str): The method to use

        json_data(Maybe[Dict[str,Any]]): Optional JSON data to pass with request

    Returns:
        Either[schema.Dump, Response]
    """
    logger.debug(f"Making {method} request to {url}")
    request_args = [method, url]
    request_kwargs: Dict[str, Any] = {"headers":{}}

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
    except requests.exceptions.ConnectionError:
        return Left(errors.connection_error(url))
    except requests.RequestException as re:
        return Left(errors.request_exception(re))

    return Right(response)

def response_check(
        check_fn: Callable[[Response],bool],
        exc_fn: Callable[[Response], schema.Dump],
        response: Response) -> Either[schema.Dump, requests.Response]:
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

ResponseCheck = Callable[[Either[schema.Dump, requests.Response]], Either[schema.Dump, requests.Response]]

def check_error(response: Response) -> Either[schema.Dump, requests.Response]:
    """
    check_error

    Checks whether a response returned a status 5xx, which signifies that the
    request resulted in an error on the remote server.
    """
    logger.debug(f"Checking if {response.url} resulted in an error")
    return response_check(lambda rsp: str(rsp.status_code)[0] != "5",
            errors.remote_error,
            response
        )

def check_404(response: Response) -> Either[schema.Dump, requests.Response]:
    """
    check_404

    Checks whether a 4xx error occurred while making the request.
    """
    return response_check(
            lambda rsp: rsp.status_code != 404,
            errors.not_found_error,
            response,
            )

def check_4xx(response: Response) -> Either[schema.Dump, requests.Response]:
    """
    check_4xx

    Checks whether a 4xx error occurred while making the request.
    """
    return response_check(
            lambda rsp: str(rsp.status_code)[0] != "4",
            errors.client_error,
            response,
            )

status_checks = [
        check_4xx,
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

    except pydantic.ValidationError:
        return Left(errors.url_parsing_error(raw))
def compose_checks(
        checks: List[ResponseCheck]
        )-> Callable[[Either[schema.Dump, requests.Response]], Either[schema.Dump, requests.Response]]:
    make_then = lambda fn: lambda x: x.then(fn)
    return compose(*[make_then(fn) for fn in checks])

def request(
        base_url: str,
        method: str,
        checks: List[ResponseCheck],
        path: str,
        parameters: Maybe[Dict[str,str]] = Nothing,
        data: Maybe[Dict[str,Any]] = Nothing
        ) -> Either[schema.Dump, Response]:
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
        Either[schema.Dump, Response]
    """

    data.then(str).then(lambda r: f"POSTing {r}").then(logger.debug)

    url = make_url(base_url, path, parameters)
    response = url.then(curry(make_request, method = method, json_data = data))
    return compose_checks(checks)(response)

def pydantic_validate(val, type):
    class mdl(pydantic.BaseModel):
        x: type
    return mdl(x=val).x
