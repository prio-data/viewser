"""
viewser.cli
===

This module defined the viewser cli, which is what is exposed when installing
the viewser package. The main entrypoint is viewser.cli.viewser. Command groups
are defined in separate modules under viewser.commands.
"""
from importlib.metadata import version
import logging
import click

from . import commands, hirearchical_dict, error_handling
from .tui.formatting import json_formatter
from .tui.formatting import errors as error_formatting

logger = logging.getLogger(__name__)

def print_version(ctx, _, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo(version("viewser"))
    ctx.exit()

@click.group()
@click.option("--debug/--no-debug", default=False, help="Display debug logging messages")
@click.option("--json/--formatted", default=False, help="Output raw data, instead of formatted data")
@click.option("--version",
        is_flag = True, callback = print_version, expose_value = False, is_eager= True)
@click.pass_context
def viewser(ctx: click.Context, debug: bool, json: bool):
    ctx.obj = hirearchical_dict.HirearchicalDict()
    if json:
        ctx.obj["table_formatter"] = json_formatter.JsonFormatter()
        ctx.obj["detail_formatter"] = json_formatter.JsonFormatter()
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)

    ctx.obj["error_dumper"] = error_formatting.ErrorFormatter()

viewser.add_command(commands.tables)
viewser.add_command(commands.transforms)
viewser.add_command(commands.queryset)
viewser.add_command(commands.config)
viewser.add_command(commands.help)
viewser.add_command(commands.logs)
viewser.add_command(commands.notebooks)
viewser.add_command(commands.system)
