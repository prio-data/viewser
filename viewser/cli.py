
from importlib.metadata import version
import logging
import json
from datetime import datetime
from typing import Optional
import io
import click
import tabulate
import requests
import views_schema
from . import settings, operations, remotes, exceptions

logger = logging.getLogger(__name__)

def print_version(ctx, _, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo(version("viewser"))
    ctx.exit()

@click.group()
@click.option("--debug/--no-debug", default=False, help="Display debug logging messages")
@click.option("--version",
        is_flag = True, callback = print_version, expose_value = False, is_eager= True)
def viewser(debug: bool):
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)

@viewser.group(name="queryset", short_help="operations related to querysets")
def queryset():
    pass

@queryset.command(name="fetch", short_help="fetch data for a queryset")
@click.argument("name")
@click.argument("out-file", type=click.File("wb"))
@click.option("-s","--start-date", type=click.DateTime())
@click.option("-e","--end-date", type=click.DateTime())
@exceptions.handle_http_exception()
def queryset_fetch(
        name:str,
        out_file:io.BufferedWriter,
        start_date: Optional[datetime],
        end_date: Optional[datetime]):
    """
    Fetch data for a queryset named NAME from ViEWS cloud and save it to OUT_FILE
    """
    click.echo(f"Fetching queryset {name}...")
    operations.fetch(name,start_date,end_date).to_parquet(out_file)
    click.echo(f"Saved to {out_file.name}")

@queryset.command(name="list", short_help="show a list of available querysets")
@click.option("--as-json/--as-table", default=False, help="output results as json")
@exceptions.handle_http_exception()
def queryset_list(as_json: bool):
    """
    Show a list of available querysets.
    """

    querysets = operations.list_querysets()
    if as_json:
        click.echo(querysets)
    else:
        click.echo(tabulate.tabulate([[qs] for qs in querysets["querysets"]],headers=["name"]))

@queryset.command(name="show", short_help="show details about a queryset")
@click.argument("name", type=str)
@exceptions.handle_http_exception()
def queryset_show(name: str):
    """
    Show detailed information about a queryset
    """
    qs = operations.show_queryset(name)
    click.echo(json.dumps(qs, indent=4))

@queryset.command(name="delete", short_help="delete a queryset")
@click.confirmation_option(prompt="Delete queryset?")
@click.argument("name", type=str)
@exceptions.handle_http_exception()
def queryset_delete(name: str):
    """
    Delete a queryset.
    """
    try:
        operations.delete_queryset(name)
        click.echo(f"Deleted {name}")
    except requests.HTTPError as httpe:
        raise click.ClickException(
                "Delete operation returned "
                f"{httpe.response.status_code}: "
                f"'{httpe.response.content.decode()}'"
            )


@queryset.command(name="upload", short_help="upload a queryset")
@click.argument("queryset_file", type=click.File("r","utf-8"))
@click.option("-n", "--name", type=str)
@click.option("--overwrite/--no-overwrite",default = False)
@exceptions.handle_http_exception()
def queryset_upload(
        queryset_file: io.BufferedReader,
        name: Optional[str],
        overwrite: bool):
    """
    Upload a queryset defined in a JSON file. The name of the queryset can be
    overridden with the --name flag.
    """
    qs = views_schema.Queryset(**json.load(queryset_file))

    if name is not None:
        click.echo(f"Renaming to {name}")
        qs.name = name

    try:
        click.echo(operations.post_queryset(qs, overwrite = overwrite))
    except (remotes.RemoteError,requests.HTTPError) as err:
        raise click.ClickException(str(err)) from err

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

@viewser.group(name="help", short_help="commands for finding documentation")
def get_help():
    """
    Commands related to finding documentation.
    """

@get_help.command(name = "wiki")
def wiki():
    """
    Open the viewser wiki in a new browser window, which contains all you need
    to know about using viewser.
    """
    remotes.browser(settings.config_get("REPO_URL"),"wiki")

@get_help.command(name = "issue")
def issue():
    """
    Opens the viewser "new issue" page in a new browser window.
    """
    remotes.browser(
            settings.config_get("REPO_URL"),
            "issue","new",
            body=f"My viewser version is {version('viewser')}"
        )
