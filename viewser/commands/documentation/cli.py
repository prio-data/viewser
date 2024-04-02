
import io
from typing import Dict, Any, Optional
import click
import pandas as pd
import json
import requests
from views_schema import docs as schema
from viewser import settings
from . import formatting, operations


@click.group(name="features", short_help="show information about available features")
@click.pass_obj
def features_cli(obj: Dict[str, Any]):
    """
    Commands used to inspect available features.
    """
#    obj["operations"] = operations.DocumentationCrudOperations(settings.config_get("REMOTE_URL"), "features")
    obj["detail_formatter"] = formatting.DocumentationDetailFormatter()
    obj["list_formatter"] = formatting.DocumentationTableFormatter()


@features_cli.command(name="list", short_help="show available features at specified loa")
@click.argument("loa")
@click.pass_obj
def list_features(obj: Dict[str, Any], loa: str):
    """
    list_features
    ===========

    Show all available features at specified loa.
    """

    obj["operations"] = operations.DocumentationCrudOperations(settings.config_get("REMOTE_URL"),
                                                               f"features/{loa}/")
    response_dict = json.loads(obj["operations"].list())['entries']
    response_df = (pd.DataFrame.from_dict(response_dict).drop(columns=['entries', 'data']).reset_index(drop=True).
                   to_string())

    click.echo(response_df)


@click.group(name="transforms")
@click.pass_obj
def transforms_cli(obj: Dict[str, Any]):
    """
    Commands used to inspect available transforms.
    """

    obj["operations"] = operations.DocumentationCrudOperations(settings.config_get("REMOTE_URL"), "transforms")
    obj["table_formatter"] = formatting.DocumentationTableFormatter()
    obj["detail_formatter"] = formatting.FunctionDetailFormatter()


@transforms_cli.command(name="list", short_help="show all available transforms")
@click.pass_obj
def list_transforms(obj: Dict[str, Any]):
    """
    List all available transforms.
    """

    response = requests.get(url=f'{settings.REMOTE_URL}/transforms')

    response_df = pd.read_parquet(io.BytesIO(response.content))

    click.echo(response_df)


@transforms_cli.command(name="at_loa", short_help="show transforms at a given loa")
@click.argument("loa", type=str)
@click.pass_obj
def show_transform(
        obj: Dict[str, Any],
        loa: str):
    """
    Show details about a transform, such as which arguments it takes, and
    which level of analysis it is applicable to.
    """

    response = requests.get(f'{settings.REMOTE_URL}/transforms/{loa}')

    response_df = pd.read_parquet(io.BytesIO(response.content))

    click.echo(response_df)


@click.group(name="transform")
@click.pass_obj
def transform_cli(obj: Dict[str, Any]):
    """
    Commands used to inspect available transforms.
    """

    obj["operations"] = operations.DocumentationCrudOperations(settings.config_get("REMOTE_URL"), "transform")
    obj["table_formatter"] = formatting.DocumentationTableFormatter()
    obj["detail_formatter"] = formatting.FunctionDetailFormatter()


@transform_cli.command(name="show", short_help="show transform detail")
@click.argument("transform_name", type=str)
@click.pass_obj
def transform(obj: Dict[str, Any], transform_name: str):
    """
    List all available transforms.
    """

    response = requests.get(url=f'{settings.REMOTE_URL}/transform/{transform_name}')

    lines = response.content.decode().strip('"').split('\\n')

    for line in lines:
        print(line)
