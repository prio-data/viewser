from collections import namedtuple
from typing import Optional
import json
import functools

import pkg_resources
import colorama
import requests
import click

def raise_pretty_exception(x: Exception):
    try:
        raise x
    except OperationPending:
        raise x
    finally:
        try:
            x.is_pretty
        except AttributeError:
            raise ViewsError(message = str(x)) from x
        else:
            raise x

def handle_http_exception(hint: str = None):
    def wrapper(fn):
        @functools.wraps(fn)
        def inner(*args,**kwargs):
            try:
                fn(*args,**kwargs)
            except(requests.HTTPError, RequestError) as err:
                raise RemoteError(
                        response = err.response,
                        hint = hint
                    )
        return inner
    return wrapper

def with_ansi(ansi):
    def wrapper(fn):
        @functools.wraps(fn)
        def inner(self,msg,*args,**kwargs):
            msg = ansi + msg + colorama.Style.RESET_ALL
            fn(self,msg,*args,**kwargs)
        return inner
    return wrapper
class PrettyFormatter(click.HelpFormatter):
    def __init__(self,*args,**kwargs):
        colorama.init()
        super().__init__(*args,**kwargs)

    @with_ansi(colorama.Fore.RED + colorama.Style.BRIGHT)
    def write_heading(self, msg):
        super().write_heading(msg)

class PrettyError(click.ClickException):
    error_name = "Error"
    is_pretty = True

    def __init__(self, message: str, hint: Optional[str] = None):
        super().__init__(self.pretty_format(message,hint))

    def pretty_format(self, message: str, hint: Optional[str] = None):
        formatter = PrettyFormatter()
        formatter.write_heading(self.error_name)
        formatter.indent()
        if message:
            with formatter.section("Description"):
                formatter.write_text(message)

        if hint:
            with formatter.section("Hint"):
                formatter.write_text(colorama.Fore.GREEN + hint + colorama.Style.RESET_ALL)

        return formatter.getvalue()

class ViewsError(PrettyError):
    error_name = "ViEWS error"

class ExistsError(PrettyError):
    """
    Raised when something is in conflict with remote,
    and an override has not been passed (--override).
    """
    error_name = "Already exists!"
    def __init__(self):
        super().__init__(self.pretty_format(
            "This resource already exists!",
            "Try passing --overwrite if you want to overwrite this resource"
            ))

class ConfigurationError(PrettyError):
    """
    Raised when something is (assumed to be) misconfigured
    """
    error_name = "Configuration error"

    def __init__(self,message: str, hint: Optional[str] = None):
        super().__init__(self.pretty_format(message, hint))

class RemoteError(PrettyError):
    """
    Raised when something goes wrong with a request
    """
    error_name = "Remote error"

    def __init__(self, response: requests.Response, hint: Optional[str] = None):
        self.response = response
        defaults_filename = pkg_resources.resource_filename("viewser","data/status-codes.json")
        with open(defaults_filename) as f:
            defaults = json.load(f)[str(response.status_code)]

        content = response.content.decode().strip()
        content = content if content else defaults["phrase"]
        content = f"{response.url} returned {response.status_code}\n\n" + content

        hint = hint if hint else defaults["description"]

        super().__init__(content, hint)

class ConnectionError(PrettyError):
    error_name = "Connection error"

    def __init__(self, url):
        super().__init__(
                    f"Could not connect to {url}",
                    (
                        "Is the config setting REMOTE_URL set to the right value?\n\n"
                        "To check, run "
                        "\n\nviewser config get REMOTE_URL.\n\n"
                        "To change the value, run "
                        "\n\nviewser config set REMOTE_URL\n\n"
                    )
                )

class UrlParsingError(PrettyError):
    error_name = "URL parsing error"
    def __init__(self, url):
        super().__init__(
                    f"Could not parse {url} as a valid http(s) url",
                    (
                        "Set the config setting REMOTE_URL to a valid http url:\n\n"
                        "viewser config set REMOTE_URL {a valid url}.\n\n"
                        "Did you forget to add http(s):// to the url?"
                    )
                )

class RequestError(PrettyError):
    def create_message(self):
        return f"\n{self.url} returned {self.status_code} \n\t({self.content})"

    def __init__(self, response, hint: Optional[str] = None):
        self.response = response
        self.url = response.url
        self.status_code = response.status_code
        self.content = response.content.decode()
        self.hint = hint
        super().__init__(self.create_message(),hint)

class OperationPending(RequestError):
    def create_message(self):
        return f"{self.url} is pending..."

class ClientError(RequestError):
    pass

class NotFoundError(RequestError):
    pass

class DeserializationError(PrettyError):
    def __init__(self, bytes):
        super().__init__(f"""
            Could not deserialize as parquet:
            \"{bytes[:50]}{'...' if len(bytes)>50 else ''}\"
        """)
