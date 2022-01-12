
from enum import Enum
from typing import Callable, List
import os
import functools
import logging
import json

import strconv
import fitin

from toolz.functoolz import compose,curry

class IRemotePaths(Enum):
    querysets = 1
    documentation = 2

logger = logging.getLogger(__name__)

REQUIRED_SETTINGS = (
            "REMOTE_URL",
        )

DEFAULT_SETTINGS = {
        "RETRY_FREQUENCY":                  5, # seconds
        "RETRIES":                          80,
        "LOG_LEVEL":                        "INFO",
        "HANDSHAKE_PATH":                   "",
        "REPO_URL":                         "https://www.github.com/prio-data/viewser",
        "LATEST_KNOWN_VERSION":             "0.0.0",
        "NOTEBOOK_SERVER_IMAGE_REPOSITORY": "prio-data/viewserspace",
        "NOTEBOOK_SERVER_IMAGE_REGISTRY":   "viewsregistry.azurecr.io",
        "ERROR_DUMP_DIRECTORY":             "dumps",
        "MODEL_OBJECT_SFTP_USER":           "predictions",
        "MODEL_OBJECT_SFTP_PORT":           22222,
        "MODEL_OBJECT_SFTP_HOSTNAME":       "hermes",
        "MODEL_OBJECT_KEY_DB_HOSTNAME":     "janus",
        "MODEL_OBJECT_KEY_DB_DBNAME":       "pred3_certs",
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

def remove_key(key,cfg):
    try:
        del cfg[key]
    except KeyError:
        logger.warning(f"Could not unset {key}, not set")
    return cfg

config_unset = lambda load,save,key: compose(
            save,
            curry(remove_key,key),
            load,
        )()

config_set = lambda load,save,key,value: compose(
        save,
        curry(with_key_value,key,value),
        load,
        )()

config_unset_in_file = curry(
        config_unset,
        load_config_from_file,
        log_decorator("Altering config file")(save_config_to_file)
        )

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

def seek_config(sources: List[Callable[[str],str]], default: Callable[[str],str])-> Callable[[str],str]:
    def seeker(key):
        for source in sources:

            try:
                return source(key)
            except KeyError:
                pass
        return default()
    return seeker

config_sources = [
    fitin.environs_resolver(),
    fitin.dict_resolver(config_dict),
    copy_to_config_file(fitin.dict_resolver(DEFAULT_SETTINGS)),
    ]

config_get = compose(
        strconv.convert,
        seek_config(config_sources,str)
        )

def is_config(key):
    try:
        value = config_get(key)
        assert value
        return True
    except (KeyError,AssertionError):
        return False

try:
    logging.basicConfig(level=getattr(logging,config_get("LOG_LEVEL")))
except(AttributeError, KeyError):
    logging.basicConfig(level=logging.INFO)

def configure_interactively():
    for setting in REQUIRED_SETTINGS:
        value = None
        while not value:
            value = input(f"{setting} >> ")
        config_set_in_file(
                setting, value
            )

REMOTE_PATHS = {
        IRemotePaths.querysets: "querysets",
        IRemotePaths.documentation: "docs",
    }

ERROR_DUMP_DIRECTORY = os.path.join(CONFIG_DIR, config_get("ERROR_DUMP_DIRECTORY"))

QUERYSET_URL = os.path.join(config_get("REMOTE_URL"), "querysets")
REMOTE_URL = config_get("REMOTE_URL")
