
import time
from typing import Optional
from io import BytesIO
import pandas as pd
import requests
from toolz.functoolz import curry
from pymonad.either import Either, Left, Right
from pymonad.maybe import Just, Nothing
from . import remotes, exceptions, animations

def deserialize(response: requests.Response) -> Either[Exception, pd.DataFrame]:
    if response.status_code == 202:
        # No data yet
        return Right(None)
    else:
        try:
            return Right(pd.read_parquet(BytesIO(response.content)))
        except OSError:
            return Left(exceptions.DeserializationError(response.content))

def fetch_queryset(
        max_retries : int,
        base_url: str, name: str,
        start_date:Optional[str] = None, end_date:Optional[str] = None
        ) -> Either[Exception, pd.DataFrame]:
    """
    fetch_queryset

    Fetches queryset located at {base_url}/querysets/data/{name}

    Args:
        base_url(str)
        name(str)
        start_date(Optional[str]): Only fetch data after start_date
        start_date(Optional[str]): Only fetch data before end_date

    Returns:
        Either[Exception, pd.DataFrame]

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

    data, error = None, None
    retries     = 0
    anim        = animations.LineAnimation()

    while not (data is not None or error is not None):
        if retries > 0:
            time.sleep(1)
        anim.print_next()

        data, error = (remotes.request(base_url, "GET", checks, path, parameters = parameters)
            .then(deserialize)
            .either(
                lambda error: (None, error),
                lambda data: (data, None),
                ))

        if retries > max_retries:
            error = exceptions.MaxRetries()

        retries += 1

    anim.end()

    if data is not None:
        return Right(data)
    else:
        return Left(error)

