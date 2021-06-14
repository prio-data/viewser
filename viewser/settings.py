from typing import Callable, List
import os
import functools
import logging
import json

import requests
import fitin
import click

from toolz.functoolz import compose,curry

from . import exceptions

logger = logging.getLogger(__name__)

def try_to_reach(url):
    try:
        rsp = requests.get(url)
        assert str(rsp.status_code)[0] == "2"
    except (
            requests.exceptions.MissingSchema,
            requests.exceptions.ConnectionError,
            requests.exceptions.ConnectTimeout,
            AssertionError
            ):
        raise exceptions.ConfigurationError(
                f"Could not reach url \"{url}\". Please enter a valid "
                "remote url."
            )
    return url

REQUIRED_SETTINGS = (
            ("REMOTE_URL", try_to_reach),
        )

DEFAULT_SETTINGS = {
        "RETRY_FREQUENCY": 5, # seconds
        "RETRIES": 80,
        "LOG_LEVEL": "INFO",
        "HANDSHAKE_PATH": "",
        "REPO_URL": "https://www.github.com/prio-data/viewser",
        "LATEST_KNOWN_VERSION": "0.0.0"
    }

CONFIG_DIR = os.path.expanduser("~/.views")
SETTINGS_FILE_PATH = os.path.join(CONFIG_DIR, "config.json")

def log_decorator(msg,level = "debug"):
    def wrapper(fn):
        functools.wraps(fn)
        def inner(*args,**kwargs):
            getattr(logger,level)(msg)
            return fn(*args,**kwargs)
        return inner
    return wrapper

def load_config_from_file():
    with open(SETTINGS_FILE_PATH) as f:
        return json.load(f)

def save_config_to_file(cfg):
    with open(SETTINGS_FILE_PATH,"w") as f:
        json.dump(cfg,f)

def with_key_value(key,value,cfg):
    cfg[key] = value
    return cfg

config_set = lambda load,save,key,value: compose(
        save,
        curry(with_key_value,key,value),
        load,
        )()

config_set_in_file = curry(
        config_set,
        load_config_from_file,
        log_decorator("Altering config file")(save_config_to_file)
        )

def reset_defaults(load,save):
    with_defaults = [curry(with_key_value,k,v) for k,v in DEFAULT_SETTINGS.items()]
    compose(
            save,
            compose(*with_defaults),
            load,
        )()

reset_config_file_defaults = curry(
        reset_defaults,
        load_config_from_file,
        save_config_to_file
        )

try:
    os.makedirs(CONFIG_DIR)
except FileExistsError:
    pass

try:
    with open(SETTINGS_FILE_PATH) as settings_file:
        config_dict = json.load(settings_file)
except FileNotFoundError:
    logger.critical("Could not find config file, please run: 'viewser config interactive'")
    config_dict = {}
    save_config_to_file(config_dict)

def copy_to_config_file(fn):
    def inner(key):
        val = fn(key)
        logger.warning(f"Writing default setting to config file: {key} - {val}")
        config_set_in_file(key,val)
        return val
    return inner

def seek_config(sources: List[Callable[[str],str]], default: Callable[[str],str])-> str:
    def seeker(key):
        for source in sources:

            try:
                return source(key)
            except KeyError:
                pass

        logger.warning(f"Key {key} not set in config")
        return default()
    return seeker

config_get = seek_config([
    fitin.environs_resolver(),
    fitin.dict_resolver(config_dict),
    copy_to_config_file(fitin.dict_resolver(DEFAULT_SETTINGS)),
    ], str)

try:
    logging.basicConfig(level=getattr(logging,config_get("LOG_LEVEL")))
except(AttributeError, KeyError):
    logging.basicConfig(level=logging.INFO)

def configure_interactively():
    for key,validate in REQUIRED_SETTINGS:
        value = None
        while not value:
            try:
                value = validate(input(f"{key} >> "))
            except exceptions.ConfigurationError as cfge:
                click.echo(str(cfge.message))
        config_set_in_file(
                key,
            )
