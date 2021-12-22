
import datetime
import io
from typing import Optional, Dict, Any

import click
from viewser.operations import queryset as queryset_operations
from viewser.tui.formatting import queryset as queryset_formatting
from viewser.error_handling import error_handling
from viewser import settings

@click.group(name="queryset", short_help="queryset_operations related to querysets")
@click.pass_obj
def queryset(ctx_obj: Dict[str, Any]):
    ctx_obj["operations"] = queryset_operations.QuerysetOperations(
            settings.QUERYSET_URL,
            error_handling.ErrorDumper([
                    error_handling.FileErrorHandler(settings.ERROR_DUMP_DIRECTORY),
                    error_handling.StreamHandler()]))
    ctx_obj["table_formatter"] = queryset_formatting.QuerysetTableFormatter()
    ctx_obj["detail_formatter"] = queryset_formatting.QuerysetDetailFormatter()

@queryset.command(name="fetch", short_help="fetch data for a queryset")
@click.argument("name")
@click.argument("out-file", type=click.File("wb"))
@click.option("-s","--start-date", type=click.DateTime())
@click.option("-e","--end-date", type=click.DateTime())
@click.pass_obj
def queryset_fetch(
        ctx_obj: Dict[str, Any],
        name:       str,
        out_file:   io.BufferedWriter,
        start_date: Optional[datetime.datetime],
        end_date:   Optional[datetime.datetime]):
    """
    Fetch data for a queryset named NAME from ViEWS cloud and save it to OUT_FILE
    """
    ctx_obj["operations"].fetch(name, out_file)

@queryset.command(name="list", short_help="show a list of available querysets")
@click.pass_obj
def queryset_list(ctx_obj: Dict[str, Any]):
    """
    Show a list of available querysets.
    """
    ctx_obj["operations"].list().then(ctx_obj["table_formatter"].formatted).then(click.echo)

@queryset.command(name="show", short_help="show details about a queryset")
@click.argument("name", type=str)
@click.pass_obj
def queryset_show(ctx_obj: Dict[str, Any], name: str):
    """
    Show detailed information about a queryset
    """
    ctx_obj["operations"].show(name).then(ctx_obj["detail_formatter"].formatted).then(click.echo).then(click.echo)

@queryset.command(name="delete", short_help="delete a queryset")
@click.confirmation_option(prompt="Delete queryset?")
@click.argument("name", type=str)
@click.pass_obj
def queryset_delete(ctx_obj: Dict[str, Any], name: str):
    """
    Delete a queryset.
    """
    ctx_obj["operations"].delete(name)
    click.echo(f"Deleted {name}")
