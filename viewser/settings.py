import os
import logging
import json
import crayons
import fitin

logger = logging.getLogger(__name__)

REQUIRED_SETTINGS = (
            "REMOTE_URL",
        )

config_dir = os.path.expanduser("~/.views")
settings_file_path = os.path.join(config_dir,"config.json")
 
try:
    try:
        os.makedirs(config_dir)
    except FileExistsError:
        pass

    with open(settings_file_path) as f:
        config_dict = json.load(f)
except FileNotFoundError:
    logger.critical(crayons.yellow("Could not find config file, "
            f"please run: {crayons.blue('viewser configure')}", bold=True))
    config_dict = {}

config = fitin.seek_config([
    fitin.environs_resolver(),
    fitin.dict_resolver(config_dict)
    ])

try:
    logging.basicConfig(level=getattr(logging,config("LOG_LEVEL")))
except(AttributeError, KeyError):
    logging.basicConfig(level=logging.INFO)
