import os
import logging
import json
import fitin

from toolz.functoolz import compose,curry

logger = logging.getLogger(__name__)

REQUIRED_SETTINGS = (
            "REMOTE_URL",
        )

DEFAULT_SETTINGS = {
        "RETRY_FREQUENCY": 5, # seconds
        "RETRIES": 80,

        "HANDSHAKE_PATH": "",
    }

CONFIG_DIR = os.path.expanduser("~/.views")
SETTINGS_FILE_PATH = os.path.join(CONFIG_DIR, "config.json")

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
        save_config_to_file
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

config_get = fitin.seek_config([
    fitin.environs_resolver(),
    fitin.dict_resolver(config_dict),
    fitin.dict_resolver(DEFAULT_SETTINGS)
    ])

try:
    logging.basicConfig(level=getattr(logging,config_get("LOG_LEVEL")))
except(AttributeError, KeyError):
    logging.basicConfig(level=logging.INFO)

def configure_interactively():
    for key in REQUIRED_SETTINGS:
        config_set_in_file(
                key,
                input(f"{key} >> "),
            )
