
import time
from typing import Optional
from io import BytesIO
import pandas as pd
import requests
from pymonad.either import Either, Left, Right
from pymonad.maybe import Just, Nothing
from views_schema import viewser as schema
from . import remotes, animations, errors

def deserialize(response: requests.Response) -> Either[Exception, pd.DataFrame]:
    if response.status_code == 202:
        # No data yet
        return Right(None)
    else:
        try:
            return Right(pd.read_parquet(BytesIO(response.content)))
        except OSError:
            return Left(errors.deserialization_error(response))

def fetch_queryset(
        max_retries : int,
        base_url: str, name: str,
        start_date:Optional[str] = None, end_date:Optional[str] = None
        ) -> Either[schema.Dump, pd.DataFrame]:
    """
    fetch_queryset

    Fetches queryset located at {base_url}/querysets/data/{name}

    Args:
        base_url(str)
        name(str)
        start_date(Optional[str]): Only fetch data after start_date
        start_date(Optional[str]): Only fetch data before end_date

    Returns:
        Either[errors.Dump, pd.DataFrame]

    """

    checks = [
                remotes.check_4xx,
                remotes.check_error,
                remotes.check_404,
             ]

    parameters = {
            k:v for k,v in {"start_date":start_date, "end_date":end_date}.items() if v is not None
            }
    parameters = Just(parameters) if len(parameters) > 0 else Nothing
    path = f"querysets/data/{name}"

    retries = 0
    anim    = animations.LineAnimation()
    data    = Right(None)

    while (data.is_right and data.value is None):
        if retries > 0:
            time.sleep(1)

        anim.print_next()

        data = (remotes.request(base_url, "GET", checks, path, parameters = parameters)
            .then(deserialize))

        if retries > max_retries:
            data = Left(errors.max_retries())

        retries += 1

    anim.end()

    return data
