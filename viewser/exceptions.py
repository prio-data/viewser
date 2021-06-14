import json
import re
import functools

import pkg_resources
import colorama
import requests
import click

def handle_http_exception(hint: str = None):
    def wrapper(fn):
        @functools.wraps(fn)
        def inner(*args,**kwargs):
            try:
                fn(*args,**kwargs)
            except requests.HTTPError as httpe:
                raise RemoteError(
                        response = httpe.response,
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

class ConfigurationError(Exception):
    """
    Raised when something is (assumed to be) misconfigured
    """

class RemoteError(click.ClickException):
    def __init__(self, response: requests.Response, hint: str = None):
        formatter = PrettyFormatter()
        formatter.write_heading(f"Remote error - {response.status_code}")
        formatter.indent()
        content = response.content.decode().strip()

        defaults_filename = pkg_resources.resource_filename("viewser","data/status-codes.json")
        with open(defaults_filename) as f:
            defaults = json.load(f)[str(response.status_code)]

        content = content if content else defaults["phrase"]
        hint = hint if hint else defaults["description"]

        with formatter.section("Description"):
            formatter.write_text(
                    "Something went wrong while making a request to "
                    f"{response.url}"
                )

        with formatter.section("Response content"):
            formatter.write_text(content)

        with formatter.section("Hint"):
            formatter.write_text(hint)

        self.message = formatter.getvalue()

        super().__init__(self.message)
