import os
from viewser import error_handling
from . import config, static

def default_error_handler():
    return error_handling.ErrorDumper([
        error_handling.FileErrorHandler(os.path.join(static.CONFIG_DIR, config.get("ERROR_DUMP_DIRECTORY"))),
        error_handling.StreamHandler()])
