
from datetime import datetime
from typing import Optional
import io
import click
import tabulate
from . import crud, settings

@click.group()
def viewser():
    pass

@viewser.group(name="queryset", short_help="operations related to querysets")
def queryset():
    pass

@queryset.command(name="fetch", short_help="fetch data for a queryset")
@click.argument("name")
@click.argument("out-file", type=click.File("wb"))
@click.option("-s","--start-date", type=click.DateTime())
@click.option("-e","--end-date", type=click.DateTime())
def queryset_fetch(
        name:str,
        out_file:io.BufferedWriter,
        start_date: Optional[datetime],
        end_date: Optional[datetime]):
    """
    Fetch data for a queryset named NAME from ViEWS cloud and save it to OUT_FILE
    """
    try:
        start_date,end_date = [dt.date() for dt in (start_date,end_date) if dt is not None]
    except ValueError:
        pass

    msg = f"Fetching queryset {name} to file {out_file.name}"
    if start_date is not None:
        msg += f" {start_date}"
    if end_date is not None:
        msg += f" {end_date}"
    click.echo(msg)

@queryset.command(name="upload", short_help="upload a queryset")
@click.argument("queryset_file", type=click.File("r","utf-8"))
@click.option("-n", "--name", type=str)
@click.option("--overwrite/--no-overwrite",default = False)
def upload_queryset(
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

@queryset.command(name="list", short_help="show a list of available querysets")
@click.option("--json",default=False, help="output results as json")
def queryset_list(json: bool):
    """
    Show a list of available querysets.
    """
    click.echo(tabulate.tabulate(
            [["a","foo",1],["b","bar",2],["c","baz",3]],
            headers = ["user","name", "date"],
        ))

@queryset.command(name="show", short_help="show details about a queryset")
@click.option("--json", default=False, help="output results as json")
@click.argument("name", type=str)
def queryset_show(name: str, json: bool):
    """
    Show detailed information about a queryset
    """
    click.echo(f"Queryset {name}...")

@queryset.command(name="delete", short_help="delete a queryset")
@click.confirmation_option(prompt="Delete queryset?")
@click.argument("name", type=str)
def queryset_delete(name: str):
    """
    Delete a queryset.
    """
    click.echo(f"Deleting Queryset {name}")

@viewser.group(name="config", short_help="configure viewser")
def config():
    """
    Configure viewser
    """

@config.command(name="interactive", short_help="interactively configure viewser")
def config_interactive():
    """
    Interactively configure viewser (useful for first-time config)
    """
    settings.configure_interactively()
    click.echo("All done!")

@config.command(name="set", short_help="set a configuration value")
@click.argument("name", type=str)
@click.argument("value", type=str)
@click.option("--override/--no-override",default=True)
def config_set(name: str, value: str, override: bool): # pylint: disable=redefined-builtin
    """
    Set a configuration value.
    """

    overrides = True
    try:
        settings.config_get(name)
    except KeyError:
        overrides = False

    if not override and overrides:
        click.echo(f"Setting {name} already set, override not specified (see --help)")
        return

    settings.config_set_in_file(name,value)
    click.echo(f"{name}: {value}")

@config.command(name="get", short_help="get a configuration value")
@click.argument("name", type=str)
def config_get(name: str):
    """
    Get a configuration value.
    """
    click.echo(f"{name}: {settings.config_get(name)}")

@config.command(name="reset", short_help="reset default config values")
@click.confirmation_option(prompt="Reset config?")
def config_reset():
    """
    Reset config, writing default values over current values.
    """
    settings.reset_config_file_defaults()
    click.echo("Config file reset")

@config.command(name="list", short_help="show all configuration settings")
def config_list():
    """
    Show all current configuration values
    """
    click.echo(tabulate.tabulate(settings.config_dict.items()))

