from typing import Dict, Any, List, Callable
import json
import webbrowser
import logging
from urllib import parse
import requests
from requests import Response
import pydantic
from pymonad.either import Left, Right, Either
from pymonad.maybe import Nothing, Maybe
from toolz.functoolz import curry, compose

from . import exceptions

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
    except requests.exceptions.ConnectionError:
        return Left(exceptions.ConnectionError(url))
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
            exceptions.OperationPending,
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

def check_specific_status(status_code: int, response: Response) -> ExceptionOrResponse:
    """
    Checks for a specific status code
    """
    return response_check(
            lambda rsp: rsp.status_code == status_code,
            curry(exceptions.RequestAssertionError, "status_code", status_code),
            response
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

    except pydantic.ValidationError:
        return Left(exceptions.UrlParsingError(raw))
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

def browser(base,*args,**kwargs):
    querystring = parse.urlencode(kwargs)
    url = "/".join([base] + list(args))
    if querystring:
        url += "?"+querystring
    webbrowser.open(url)

