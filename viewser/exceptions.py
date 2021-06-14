from typing import Optional
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

class PrettyError(Exception):
    error_name = "Error"

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


class ConfigurationError(click.ClickException,PrettyError):
    """
    Raised when something is (assumed to be) misconfigured
    """
    error_name = "Configuration error"

    def __init__(self,message: str, hint: Optional[str] = None):
        super().__init__(self.pretty_format(message, hint))

class RemoteError(click.ClickException, PrettyError):
    """
    Raised when something goes wrong with a request
    """
    error_name = "Remote error"

    def __init__(self, response: requests.Response, hint: Optional[str] = None):
        defaults_filename = pkg_resources.resource_filename("viewser","data/status-codes.json")
        with open(defaults_filename) as f:
            defaults = json.load(f)[str(response.status_code)]

        content = response.content.decode().strip()
        content = content if content else defaults["phrase"]
        content = f"{response.url} returned {response.status_code}\n\n" + content

        hint = hint if hint else defaults["description"]

        super().__init__(
                self.pretty_format(content, hint)
            )
