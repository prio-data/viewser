from collections import defaultdict
from typing import Optional
import json
import functools

import pkg_resources
import colorama
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
    def write_heading(self, heading):
        super().write_heading(heading)

class PrettyError(click.ClickException):
    error_name = "Error"
    is_pretty = True
    DEFAULT_HINT = None

    def __init__(self, message: str, hint: Optional[str] = None):
        hint = hint if hint else (self.DEFAULT_HINT if self.DEFAULT_HINT else None)
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

class DeserializationError(PrettyError):
    error_name = "DeserializationError"

    def __init__(self, bytes):
        super().__init__(f"""
            Could not deserialize as parquet:
            \"{bytes[:50]}{'...' if len(bytes)>50 else ''}\"
        """)

class RequestError(PrettyError):
    error_name = "Request error"

    def _http_default_hints(self):
        return {}

    def http_defaults(self, status_code):
        return defaultdict(str, self._http_default_hints().get(str(status_code)))

    def make_message(self):
        return self.content

    def __init__(self, response, hint: Optional[str] = None):
        self.response = response
        self.url = response.url
        self.status_code = response.status_code

        defaults = self.http_defaults(self.status_code)

        self.content = response.content.decode().strip() if response.content else defaults["phrase"]
        self.hint = hint if hint is not None else defaults["description"]
        super().__init__(self.content, self.hint)

class OperationPending(RequestError):
    error_name = "Pending..."

class ClientError(RequestError):
    error_name = "4xx client error"

class NotFoundError(RequestError):
    error_name = "404 not found"

class RemoteError(RequestError):
    error_name = "5xx remote error"

class RequestAssertionError(RequestError):
    error_name = "Assertion error"
    def __init__(self, attr, expected, response):
        self.attr = attr
        self.expected = expected
        self.actual = getattr(attr, response)
        super().__init__(response)

    def make_message(self):
        return (
                f"Response {self.attr} had unexpected value: "
                f"Expected {self.expected}, got {self.actual}"
            )

class ViewserspaceError(PrettyError):
    error_name = "Viewserspace error"
    DEFAULT_HINT = """
These errors are usually related to Docker / Azure ACR authentication. Make
sure that you have installed the credentials file in the proper location
(~/.views/sp.json), and that the credentials are correct. Talk to an admin for
credentials.
    """

    def __init__(self, message, hint: Optional[str] = None):
        hint = hint if hint is not None else self.DEFAULT_HINT
        super().__init__(message, hint)

def exception_raiser(exception:Exception, *args, **kwargs):
    e = exception(*args, **kwargs)
    raise e

class MaxRetries(PrettyError):
    error_name = "Max retries"

    DEFAULT_HINT = """
Your request reached the currently configured maximum number of retries.
To increase the limit for max retries, run this command:

viewser config set MAX_RETRIES { a bigger number }
    """

    def __init__(self):
        super().__init__("Max number of retries reached")
