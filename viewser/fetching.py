
from typing import Optional
from io import BytesIO
import pandas as pd
import requests
from toolz.functoolz import curry
from pymonad.either import Either, Left, Right
from pymonad.maybe import Just, Nothing
from . import remotes, exceptions

def deserialize(response: requests.Response) -> Either[Exception, pd.DataFrame]:
    try:
        return Right(pd.read_parquet(BytesIO(response.content)))
    except OSError:
        return Left(exceptions.DeserializationError(response.content))

def fetch_queryset(base_url: str, name: str,
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
                curry(remotes.check_content_type, "application/octet-stream"),
                remotes.check_pending,
                remotes.check_4xx,
                remotes.check_error,
                remotes.check_404,
             ]
    request = curry(remotes.request,base_url,"GET",checks)
    parameters = {
            k:v for k,v in {"start_date":start_date, "end_date":end_date}.items() if v is not None
            }
    parameters = Just(parameters) if len(parameters) > 0 else Nothing
    path = f"querysets/data/{name}"

    return (request(path, parameters = parameters)
            .then(deserialize)
            )
