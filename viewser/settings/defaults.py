from viewser import error_handling
from . import config

def default_error_handler():
    return error_handling.ErrorDumper([
        error_handling.FileErrorHandler(config.get("ERROR_DUMP_DIRECTORY")),
        error_handling.StreamHandler()])
