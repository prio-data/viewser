
import io
import click
import pandas as pd
import requests
from viewser import settings


@click.group(name="features", short_help="show information about available features")
def features_cli():
    """
    Commands used to inspect available features.
    """


@features_cli.command(name="list", short_help="show available features at specified loa")
@click.argument("loa")
def list_features(loa: str):
    """
    list_features
    ===========

    Show all available features at specified loa.

    Response currently comes as a string - sending a df fails (empty parquet file) - reason unknown
    """

    response = requests.get(url=f'{settings.REMOTE_URL}/features/{loa}')

    lines = str(response.content.decode()).strip('"').split("\\n")

    features = []
    loas = []

    for line in lines[:-1]:
        feature, loa = line.split(',')[0], line.split(',')[1]
        features.append(feature)
        loas.append(loa)

    response_df = pd.DataFrame({'feature': features, 'loa hint': loas})

    print(response_df.to_string())


@click.group(name="transforms")
def transforms_cli():
    """
    Commands used to inspect available transforms.
    """


@transforms_cli.command(name="list", short_help="show all available transforms")
def list_transforms():
    """
    List all available transforms.
    """

    response = requests.get(url=f'{settings.REMOTE_URL}/transforms')

    try:
        response_df = pd.read_parquet(io.BytesIO(response.content))
    except:
        response_df = pd.DataFrame()

    click.echo(response_df)


@transforms_cli.command(name="at_loa", short_help="show transforms at a given loa")
@click.argument("loa", type=str)
def show_transform(loa: str):
    """
    Show details about a transform, such as which arguments it takes, and
    which level of analysis it is applicable to.
    """

    response = requests.get(url=f'{settings.REMOTE_URL}/transforms/{loa}')

    try:
        response_df = pd.read_parquet(io.BytesIO(response.content))
    except:
        response_df = pd.DataFrame()

    click.echo(response_df)


@click.group(name="transform")
def transform_cli():
    """
    Commands used to inspect available transforms.
    """


@transform_cli.command(name="show", short_help="show transform detail")
@click.argument("transform_name", type=str)
def transform(transform_name: str):
    """
    List all available transforms.
    """

    response = requests.get(url=f'{settings.REMOTE_URL}/transform/{transform_name}')

    lines = response.content.decode().strip('"').split('\\n')

    for line in lines:
        print(line)
