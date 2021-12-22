import io
from typing import Dict, Any, Optional
import click
from views_schema import docs as schema
from viewser import settings
from viewser.operations import documentation as documentation_operations
from viewser.tui.formatting import documentation as documentation_formatting

@click.group(name = "tables", short_help = "show information about available tables")
@click.pass_obj
def tables(ctx_obj: Dict[str, Any]):
    """
    Commands used to inspect available tables and columns.
    """
    ctx_obj["operations"]       = documentation_operations.DocumentationCrudOperations(settings.config_get("REMOTE_URL"), "tables")
    ctx_obj["detail_formatter"] = documentation_formatting.DocumentationDetailFormatter()
    ctx_obj["list_formatter"]   = documentation_formatting.DocumentationTableFormatter()

@tables.command(name="list", short_help="show available tables")
@click.pass_obj
def list_tables(ctx_obj: Dict[str, Any]):
    """
    Show all available tables.
    """

    result = ctx_obj["operations"].list()
    click.echo(ctx_obj["list_formatter"].formatted(result))

@tables.command(name="show", short_help="inspect table or column")
@click.argument("table-name")
@click.argument("column-name", required=False)
@click.pass_obj
def show_tables(
        ctx_obj: Dict[str, Any],
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
        formatter = ctx_obj["detail_formatter"]
    else:
        formatter = ctx_obj["list_formatter"]

    result = ctx_obj["operations"].show(path)
    click.echo(formatter.formatted(result))

@tables.command(name="annotate", short_help="add documentation text")
@click.argument("content-file", type=click.File("r"))
@click.argument("table-name")
@click.argument("column-name", required=False)
@click.option("--overwrite", is_flag = True, help="overwrite existing documentation")
@click.pass_obj
def annotate_table(
        ctx_obj: Dict[str, Any],
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
        formatter = ctx_obj["detail_formatter"]
    else:
        formatter = ctx_obj["list_formatter"]

    to_post = schema.PostedDocumentationPage(content = content_file.read())

    result = ctx_obj["operations"].post(to_post, path, overwrite = overwrite)

    click.echo(formatter.formatted(result))
