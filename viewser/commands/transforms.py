import io
from typing import Dict, Any
import click
import views_schema
from viewser import settings
from viewser.operations import documentation as documentation_operations
from viewser.tui.formatting import documentation as documentation_formatting

@click.group(name="transforms")
@click.pass_obj
def transforms(ctx_obj: Dict[str, Any]):
    """
    Commands used to inspect available transforms.
    """

    ctx_obj["operations"] = documentation_operations.DocumentationCrudOperations(
            settings.config_get("REMOTE_URL"), "transforms")
    ctx_obj["table_formatter"] = documentation_formatting.DocumentationTableFormatter()
    ctx_obj["detail_formatter"] = documentation_formatting.FunctionDetailFormatter()

@transforms.command(name="list", short_help="show all available transforms")
@click.pass_obj
def list_transforms(ctx_obj: Dict[str, Any]):
    """
    List all available transforms.
    """
    help = (
            "Run viewser transforms show {path} "
            "to see details about a transform, "
            "such as its list of arguments and "
            "docstring."
        )

    result = ctx_obj["operations"] .list()
    click.echo(ctx_obj["table_formatter"].formatted(result))

@transforms.command(name="show",short_help="show details about a transform")
@click.argument("transform-name", type=str)
@click.pass_obj
def show_transform(
        ctx_obj: Dict[str, Any],
        transform_name: str):
    """
    Show details about a transform, such as which arguments it takes, and
    which level of analysis it is applicable to.
    """
    result = ctx_obj["operations"].show(transform_name)
    click.echo(ctx_obj["detail_formatter"].formatted(result))

@transforms.command(name="annotate", short_help="add documentation text")
@click.argument("content-file", type=click.File("r"))
@click.argument("transform-name")
@click.option("--overwrite", is_flag = True, help="overwrite existing documentation")
@click.pass_obj
def annotate_transform(
        ctx_obj: Dict[str, Any],
        content_file: io.BufferedReader,
        transform_name: str,
        overwrite: bool = False):
    """
    Annotate a table or a column. To annotate a table, pass a single argument
    following the file containing the annotation. To annotate a column, pass
    two arguments.
    """
    to_post = views_schema.docs.PostedDocumentationPage(content = content_file.read())
    result = ctx_obj["operations"].post(to_post, transform_name, overwrite=overwrite)
    click.echo(ctx_obj["detail_formatter"].formatted(result))
