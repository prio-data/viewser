
import sys
import webbrowser
from importlib.metadata import version
import logging
import json
from datetime import datetime
from typing import Optional
import io

from toolz.functoolz import identity
from pymonad.maybe import Nothing, Just
import docker
import click
import tabulate
import requests
import views_schema
from . import settings, operations, remotes, exceptions, crud, formatting, context_objects, notebooks, ascii_art

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

def queryset_show(name: str):
    """
    Show detailed information about a queryset
    """
    qs = operations.show_queryset(name)
    click.echo(json.dumps(qs, indent=4))

@queryset.command(name="delete", short_help="delete a queryset")
@click.confirmation_option(prompt="Delete queryset?")
@click.argument("name", type=str)
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

    click.echo(operations.publish_queryset(qs, overwrite = overwrite))

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
@click.argument("value", type=str, default=1)
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
    value = settings.config_get(name)
    if value:
        click.echo(f"{name}: {value}")
    else:
        click.echo(f"{name} not set")
        sys.exit(1)

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

@config.command(name="unset", short_help="unset a configuration value")
@click.confirmation_option(prompt="Unset config key?")
@click.argument("name", type=str)
def config_unset(name: str):
    """
    Unset a configuration value, removing its entry from the config file.
    """
    current_value = settings.config_get(name)
    settings.config_unset_in_file(name)
    click.echo(f"Unset {name} (was {current_value})")

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

@viewser.group(name="tables")
@click.pass_context
def tables(ctx: click.Context):
    """
    Commands used to inspect available tables and columns.
    """
    ctx.obj = context_objects.DocumentationContext(
                crud.DocumentationCrudOperations(settings.config_get("REMOTE_URL"), "tables"),
                formatting.DocumentationFormatter()
            )

@tables.command(name="list", short_help="show available tables")
@click.pass_obj
def list_tables(ctx_obj: context_objects.DocumentationContext):
    """
    Show all available tables.
    """
    help = (
            "Run viewser tables show {table} to see "
            "what columns are in a table. To see "
            "more information about a column, run "
            "viewser tables show {table} {column}."
        )

    click.echo(
        ctx_obj.format(
            ctx_obj.operations.list(),
            (
                ("", formatting.title),
                ("", formatting.entry_table),
                ("", formatting.help_string(help)) if settings.is_config("VERBOSE") else None,
            )
        )
    )

@tables.command(name="show", short_help="inspect table or column")
@click.argument("table-name")
@click.argument("column-name", required=False)
@click.pass_obj
def show_tables(
        ctx_obj: context_objects.DocumentationContext,
        table_name: str,
        column_name: Optional[str] = None):
    """
    Show either a table or a column, depending on whether one argument is
    passed (table name), or two arguments are passed (table name - column
    name).
    """
    path = table_name
    if column_name:
        path += "/"+column_name
    click.echo(
        ctx_obj.format(
            ctx_obj.operations.show(path),
            (
                ("", formatting.title),
                ("Description", formatting.description),
                ("Columns", formatting.entry_table) if column_name is None else None
            )
        )
    )

@tables.command(name="annotate", short_help="add documentation text")
@click.argument("content-file", type=click.File("r"))
@click.argument("table-name")
@click.argument("column-name", required=False)
@click.option("--overwrite", is_flag = True, help="overwrite existing documentation")
@click.pass_obj
def annotate_table(
        ctx_obj: context_objects.DocumentationContext,
        content_file: io.BufferedReader,
        table_name: str,
        column_name: str,
        overwrite: bool):
    """
    Annotate a table or a column. To annotate a table, pass a single argument
    following the file containing the annotation. To annotate a column, pass
    two arguments.
    """
    path = table_name
    if column_name:
        path += "/"+column_name

    to_post = views_schema.PostedDocumentationPage(content = content_file.read())
    posted = ctx_obj.operations.post(to_post, path, overwrite = overwrite)
    click.echo(ctx_obj.format(
            posted,
            (
                ("", formatting.title),
                ("Description", formatting.description)
            )
        )
    )

@viewser.group(name="transforms")
@click.pass_context
def transforms(ctx: click.Context):
    """
    Commands used to inspect available transforms.
    """
    ctx.obj = context_objects.DocumentationContext(
                crud.DocumentationCrudOperations(settings.config_get("REMOTE_URL"), "transforms"),
                formatting.DocumentationFormatter()
            )

@transforms.command(name="list", short_help="show all available transforms")
@click.pass_obj
def list_transforms(ctx_obj: crud.DocumentationCrudOperations):
    """
    List all available transforms.
    """
    help = (
            "Run viewser transforms show {path} "
            "to see details about a transform, "
            "such as its list of arguments and "
            "docstring."
        )

    click.echo(
        ctx_obj.format(
            ctx_obj.operations.list(),
            (
                ("", formatting.title),
                ("", formatting.entry_table),
                ("", formatting.help_string(help)) if settings.is_config("VERBOSE") else None,
            )
        )
    )

@transforms.command(name="show",short_help="show details about a transform")
@click.argument("transform-name", type=str)
@click.pass_obj
def show_transform(
        ctx_obj: context_objects.DocumentationContext,
        transform_name: str):
    """
    Show details about a transform, such as which arguments it takes, and
    which level of analysis it is applicable to.
    """
    click.echo(
        ctx_obj.format(
            ctx_obj.operations.show(transform_name),
            (
                ("", formatting.title),
                ("Description", formatting.description),
                ("", formatting.function_sig),
            )
        )
    )

@transforms.command(name="annotate", short_help="add documentation text")
@click.argument("content-file", type=click.File("r"))
@click.argument("transform-name")
@click.option("--overwrite", is_flag = True, help="overwrite existing documentation")
@click.pass_obj
def annotate_transform(
        ctx_obj: context_objects.DocumentationContext,
        content_file: io.BufferedReader,
        transform_name: str,
        overwrite: bool = False):
    """
    Annotate a table or a column. To annotate a table, pass a single argument
    following the file containing the annotation. To annotate a column, pass
    two arguments.
    """
    to_post = views_schema.PostedDocumentationPage(content = content_file.read())
    posted = ctx_obj.operations.post(to_post, transform_name, overwrite=overwrite)
    click.echo(ctx_obj.format(
            posted,
            (
                ("", formatting.title),
                ("Description", formatting.description)
            )
        )
    )

@viewser.group(name="notebooks", short_help="run ipython notebooks")
def notebook_commands():
    pass

@notebook_commands.command(name="run", short_help="start the viewserspace ipython notebook server")
@click.option("-r","--requirements-file", type = str, default = None, help = "Optional requirements file")
@click.option("-w","--work-dir", type = str, default = ".", help = "Directory to mount")
@click.option("-v","--use-version", type = str, default="latest", help="Image version to use")
@click.option("--browser/--no-browser", type = bool, default=True, help="Automatically open a browser window")
@click.option("--pull/--no-pull", type = bool, default=True, help="Check for environment updates")
def run_viewserspace(
        use_version: str,
        requirements_file: str,
        work_dir: str,
        browser: bool,
        pull: bool,
        ):

    requirements_file = Just(requirements_file) if requirements_file else Nothing
    port = notebooks.seek_port(notebooks.START_PORT)

    if not port:
        click.echo("No available ports")
        return

    image = notebooks.notebook_image(
            "viewsregistry.azurecr.io",
            settings.config_get("NOTEBOOK_SERVER_IMAGE_REPOSITORY"),
            use_version,
            pull)

    container_id, container_url = notebooks.run_notebook_server(
            port,
            image,
            work_dir,
            requirements_file,
        )

    click.echo(ascii_art.VIEWSERSPACE_LOGO)

    print("Server running. Ctrl-C to stop.")
    if browser:
        webbrowser.open(container_url)
    else:
        print(f"To access, open {container_url}")

    try:
        while True:
            pass
    finally:
        container = docker.client.from_env().containers.get(container_id)
        container.kill()
