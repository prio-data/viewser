
from . import db, models, config_resolver, static

models.metadata.create_all(db.engine)
config = config_resolver.ConfigResolver(db.Session)
config.load(static.DEFAULT_SETTINGS, overwrite = False)

get_config = config.get_config
