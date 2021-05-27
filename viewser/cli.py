
from typing import Optional
import io
import click
import tabulate

@click.group()
def viewser():
    pass

@viewser.group(short_help="operations related to querysets")
def queryset():
    pass

@queryset.command(short_help="fetch data for a queryset")
@click.argument("name")
@click.argument("outfile", type=click.File("wb"))
def fetch(name:str, outfile:io.BufferedWriter):
    """
    Fetch data for a queryset named NAME from ViEWS cloud and save it to OUT_FILE
    """
    click.echo(f"Fetching queryset {name} to file {outfile.name}")

@queryset.command(short_help="upload a queryset")
@click.argument("queryset_file", type=click.File("r","utf-8"))
@click.option("-n", "--name", type=str)
@click.option("--overwrite/--no-overwrite",default = False)
def upload(
        queryset_file: io.BufferedReader,
        name: Optional[str],
        overwrite: bool):
    """
    Upload a queryset defined in a JSON file. The name of the queryset can be
    overridden with the --name flag.
    """
    if name is not None:
        click.echo(f"Renaming to {name}")

    if overwrite:
        click.echo("Overwriting!")

    click.echo(f"Uploading queryset from file {queryset_file.name}")

@queryset.command(short_help="show a list of available querysets")
@click.option("--json",default=False, help="output results as json")
def list(json: bool): # pylint: disable=redefined-builtin
    """
    Show a list of available querysets.
    """
    click.echo(tabulate.tabulate(
            [["a","foo",1],["b","bar",2],["c","baz",3]],
            headers = ["user","name", "date"],
        ))

@queryset.command(short_help="show details about a queryset")
@click.option("--json", default=False, help="output results as json")
@click.argument("name", type=str)
def show(name: str, json: bool):
    """
    Show detailed information about a queryset
    """
    click.echo(f"Queryset {name}...")

@queryset.command(short_help="delete a queryset")
@click.confirmation_option(prompt="Are you sure?")
@click.argument("name", type=str)
def delete(name: str):
    """
    Delete a queryset.
    """
    click.echo(f"Deleting Queryset {name}")

@viewser.group(short_help="configure viewser")
def configure():
    """
    Configure viewser
    """
    pass

@configure.command(short_help="interactively configure viewser")
def interactive():
    """
    Interactively configure viewser (useful for first-time config)
    """
    click.echo("Configuring...")

@configure.command(short_help="set a configuration value")
@click.argument("name", type=str)
@click.argument("value", type=str)
@click.option("--override/--no-override",default=True)
def set(name: str, value: str, override: bool):
    """
    Set a configuration value
    """
    if override:
        click.echo("Overriding existing value")

    click.echo(f"Setting {name} to {value}")

@configure.command(short_help="get a configuration value")
@click.argument("name", type=str)
def get(name: str):
    """
    Get a configuration value
    """
    click.echo(f"Getting config value {name}")
