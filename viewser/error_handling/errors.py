
import logging
from typing import Callable
import base64
import json
import datetime
import pydantic
import requests
from views_schema import viewser as schema

logger = logging.getLogger(__name__)

def response_as_json(response: requests.Response):
    """
    response_as_json
    ================

    Return a response in json form, used for dumping response contents.
    """
    try:
        content = response.content.decode()
    except UnicodeDecodeError:
        content = base64.b64encode(response.content).decode()

    return json.dumps({
            "url":         response.url,
            "http_status": response.status_code,
            "content":     content,
        })

def try_to_propagate(function: Callable[[requests.Response], schema.Dump])-> Callable[[requests.Response], schema.Dump]:
    """
    try_to_propagate
    ================

    Try to propagate an error dump from the remote, before running the local
    function to produce a fallback error.
    """
    def inner(response: requests.Response) -> schema.Dump:
        try:
            error = schema.Dump(**response.json())
            logger.debug("Propagating error from remote")
            return error 
        except (json.JSONDecodeError, pydantic.ValidationError):
            logger.debug(f"Failed to propagate error from response: \"{response.content[:25]}...\"")
            return function(response)
    return inner

def max_retries():
    return schema.Dump(
            title = "Max number of retries!",
            timestamp = datetime.datetime.now(),
            messages = [
                    schema.Message(
                            message_type = schema.MessageType.MESSAGE,
                            content = ("You reached the maximum number of "
                                "retries while waiting for data." )),
                    schema.Message(
                            message_type = schema.MessageType.HINT,
                            content = ("Try increasing the max. allowed number "
                                "of retries by running `viewser config RETRIES "
                                "{larger_number}"))
                ])

def connection_error(url: str):
    return schema.Dump(
            title = "Connection error!",
            timestamp = datetime.datetime.now(),
            messages = [
                    schema.Message(
                            message_type = schema.MessageType.MESSAGE,
                            content = (f"You failed to connect to {url}.")),
                    schema.Message(
                            message_type = schema.MessageType.HINT,
                            content = ("Is the REMOTE_URL correct? View the "
                                "currently set REMOTE_URL by running viewser "
                                "config show REMOTE_URL. Change it with viewser "
                                "config set REMOTE_URL."))
                ])

@try_to_propagate
def remote_error(response: requests.Response):
    return schema.Dump(
            title = "500 remote error",
            timestamp = datetime.datetime.now(),
            messages = [
                    schema.Message(
                        content = "Internal server error!"
                        ),

                    schema.Message(
                        message_type = schema.MessageType.HINT,
                        content = ("This kind of error is caused by something "
                            "going wrong on the server. Please contact and "
                            "administrator right away.")
                        ),

                    schema.Message(
                        message_type = schema.MessageType.DUMP,
                        content = response_as_json(response)
                        )
                ])

@try_to_propagate
def not_found_error(response: requests.Response):
    return schema.Dump(
            title = "404 not found",
            timestamp = datetime.datetime.now(),
            messages = [
                    schema.Message(
                        content = (f"The url {response.url} refers to a resource "
                        "that does not exist on the server.")),
                    schema.Message(
                        message_type = schema.MessageType.HINT,
                        content = "Did you mistype something?"),
                ])

@try_to_propagate
def client_error(response: requests.Response):
    return schema.Dump(
            title = f"{response.status_code} client error",
            timestamp = datetime.datetime.now(),
            messages = [
                    schema.Message(
                        content = ("The request was not accepted by the server, because it did not have the right format.")),
                    schema.Message(
                        message_type = schema.MessageType.HINT,
                        content = ("These messages might be caused by using an "
                        "old version of viewser that is not supported by the "
                        "currently running server version. Try updating viewser "
                        "with pip install --upgrade viewser. "
                        "It might also be caused by misspelling a column name, "
                        "a table name, or a transform name."
                        )),
                ])

def url_parsing_error(url: str):
    return schema.Dump(
            title = "Failed to parse URL",
            timestamp = datetime.datetime.now(),
            messages = [
                    schema.Message(
                        content = (f"Failed to parse url: {url}")),
                    schema.Message(
                        message_type = schema.MessageType.HINT,
                        content = ("This is indicative of an issue with "
                            "viewser. Contact an admin and copy-paste this error "
                            "message.")),
                ])

def request_exception(exception: requests.RequestException):
    return schema.Dump(
            title = f"{str(exception)}",
            timestamp = datetime.datetime.now(),
            messages = [
                    schema.Message(
                        content = ("Encountered an unhandled exception while making a request."))
                ])

def deserialization_error(response: requests.Response):
    return schema.Dump(
            title = "Deserialization error",
            timestamp = datetime.datetime.now(),
            messages = [
                    schema.Message(
                        content = ("Failed to deserialize data from response "
                            "content. The response had HTTP status "
                            f"{response.status_code}.")),
                    schema.Message(
                        message_type = schema.MessageType.DUMP,
                        content = (response_as_json(response))),
                ]
            )

def exists_error(resource_name: str):
    return schema.Dump(
            title = "Resource exists",
            timestamp = datetime.datetime.now(),
            messages = [
                    schema.Message(
                            content = f"Resource {resource_name} already exists"
                        ),
                ])
