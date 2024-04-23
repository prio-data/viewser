
import datetime
import io
import pandas as pd
from typing import Optional, Dict, Any

import click
from viewser import settings
from viewser.settings import defaults
from . import operations, formatting


@click.group(name="queryset", short_help="queryset_operations related to querysets")
@click.pass_obj
def cli(ctx_obj: Dict[str, Any]):
    ctx_obj["operations"] = operations.QuerysetOperations(
            settings.QUERYSET_URL,
            defaults.default_error_handler(),
            settings.QUERYSET_MAX_RETRIES,
            )
    ctx_obj["table_formatter"] = formatting.QuerysetTableFormatter()
    ctx_obj["detail_formatter"] = formatting.QuerysetDetailFormatter()


@cli.command(name="fetch", short_help="fetch data for a queryset")
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


@cli.command(name="list", short_help="show a list of available querysets")
@click.pass_obj
def queryset_list(ctx_obj: Dict[str, Any]):
    """
    Show a list of available querysets.
    """
    result_df = pd.DataFrame(ctx_obj["operations"].list(), columns=['querysets', ])

    print(result_df.to_string())


@cli.command(name="show", short_help="show code for a queryset")
@click.argument("name", type=str)
@click.pass_obj
def queryset_show(ctx_obj: Dict[str, Any], name: str):
    """
    Show detailed information about a queryset
    """

    click.echo(ctx_obj["operations"].show(name))


@cli.command(name="delete", short_help="delete a queryset")
@click.confirmation_option(prompt="Delete queryset?")
@click.argument("name", type=str)
@click.pass_obj
def queryset_delete(ctx_obj: Dict[str, Any], name: str):
    """
    Delete a queryset.
    """
    ctx_obj["operations"].delete(name)
    click.echo(f"Deleted {name}")
