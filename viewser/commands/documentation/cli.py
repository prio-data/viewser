
import io
from typing import Dict, Any, Optional
import click
import pandas as pd
import json
from views_schema import docs as schema
from viewser import settings
from . import formatting, operations

@click.group(name = "tables", short_help = "show information about available tables")
@click.pass_obj
def tables_cli(obj: Dict[str, Any]):
    """
    Commands used to inspect available tables and columns.
    """
    obj["operations"]       = operations.DocumentationCrudOperations(settings.config_get("REMOTE_URL"), "tables")
    obj["detail_formatter"] = formatting.DocumentationDetailFormatter()
    obj["list_formatter"]   = formatting.DocumentationTableFormatter()

@tables_cli.command(name="list", short_help="show available tables")
@click.pass_obj
def list_tables(obj: Dict[str, Any]):
    """
    list_tables
    ===========

    Show all available tables.
    """

    response_dict = json.loads(obj["operations"].list())['entries']
    response_df = pd.DataFrame.from_dict(response_dict)['name'].sort_values().reset_index(drop=True).to_string()

    click.echo(response_df)

@tables_cli.command(name="show", short_help="inspect table or column")
@click.argument("table-name")
@click.argument("column-name", required=False)
@click.pass_obj
def show_tables(
        obj: Dict[str, Any],
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
        formatter = obj["detail_formatter"]
    else:
        formatter = obj["list_formatter"]

    response_dict = json.loads(obj["operations"].show(path))['entries']

    response_df = pd.DataFrame.from_dict(response_dict)['name'].sort_values().reset_index(drop=True).to_string()

    click.echo(response_df)

@tables_cli.command(name="annotate", short_help="add documentation text")
@click.argument("content-file", type=click.File("r"))
@click.argument("table-name")
@click.argument("column-name", required=False)
@click.option("--overwrite", is_flag = True, help="overwrite existing documentation")
@click.pass_obj
def annotate_table(
        obj: Dict[str, Any],
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
        formatter = obj["detail_formatter"]
    else:
        formatter = obj["list_formatter"]

    to_post = schema.PostedDocumentationPage(content = content_file.read())

    click.echo(obj["operations"].post(to_post, path, overwrite = overwrite)
        .either(obj["error_dumper"].formatted, formatter.formatted))

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
    response_dict = json.loads(obj["operations"].list())['entries']
    response_df = pd.DataFrame.from_dict(response_dict)['path'].sort_values().reset_index(drop=True).to_string()
    click.echo(response_df)

@transforms_cli.command(name="show",short_help="show details about a transform")
@click.argument("transform-name", type=str)
@click.pass_obj
def show_transform(
        obj: Dict[str, Any],
        transform_name: str):
    """
    Show details about a transform, such as which arguments it takes, and
    which level of analysis it is applicable to.
    """

    response_dict = json.loads(obj["operations"].show(transform_name))

    if len(response_dict['entries'])>0:
        response_df = pd.DataFrame.from_dict(response_dict['entries'])['path'].sort_values().reset_index(drop=True).to_string()
        click.echo(response_df)
    else:
        click.echo(response_dict['data']['docstring'])


@transforms_cli.command(name="annotate", short_help="add documentation text")
@click.argument("content-file", type=click.File("r"))
@click.argument("transform-name")
@click.option("--overwrite", is_flag = True, help="overwrite existing documentation")
@click.pass_obj
def annotate_transform(
        obj: Dict[str, Any],
        content_file: io.BufferedReader,
        transform_name: str,
        overwrite: bool = False):
    """
    Annotate a table or a column. To annotate a table, pass a single argument
    following the file containing the annotation. To annotate a column, pass
    two arguments.
    """
    to_post = schema.PostedDocumentationPage(content = content_file.read())
    click.echo(obj["operations"].post(to_post, transform_name, overwrite=overwrite)
        .either(obj["error_dumper"].formatted, obj["detail_formatter"].formatted))
