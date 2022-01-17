import os
from . import db, models, config_resolver, static

models.metadata.create_all(db.engine)
config = config_resolver.ConfigResolver(db.Session)
config.load(static.DEFAULT_SETTINGS, overwrite = False)

config_get = config.get

# =Remotes================================================

REMOTE_URL = config.get("REMOTE_URL") or "http://0.0.0.0:4000"
QUERYSET_URL = os.path.join(REMOTE_URL, "querysets")

QUERYSET_MAX_RETRIES = config.get("QUERYSET_MAX_RETRIES")

# =Compatibility==========================================

def reset_defaults():
    config.load(static.DEFAULT_SETTINGS, overwrite = True)

def configure_interactively():
    for setting in static.REQUIRED_SETTINGS:
        value = None
        while not value:
            value = input(f"{setting} >> ")
        config.set(setting, value)
