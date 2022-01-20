"""
Compatibility
"""
from typing import Optional
from datetime import date
import pandas as pd
from viewser import settings
from viewser.settings import defaults
from viewser.commands.queryset import operations

def fetch(queryset_name: str, start_date: Optional[date] = None, end_date: Optional[date] = None) -> Optional[pd.DataFrame]:
    """
    fetch
    =====

    parameters:
        queryset_name (str)

    returns:
        pandas.DataFrame

    Fetch a queryset

    """
    return operations.QuerysetOperations(
            settings.QUERYSET_URL,
            defaults.default_error_handler(),
            settings.QUERYSET_MAX_RETRIES,
            ).fetch(queryset_name).maybe(None, lambda x:x)
