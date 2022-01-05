
import os
import json
import click
from views_schema import viewser as schema
from viewser import settings
from . import formatting
from . import models

@click.group(name = "system", short_help = "administration commands")
def cli():
    """
    Admin commands.
    """

@cli.group(name = "error", short_help = "commands related to error dumps")
@click.pass_context
def error(ctx: click.Context):
    """
    Commands related to error dumps.
    """
    ctx.obj["errors"] = models.ErrorDumpFiles.from_dir(settings.ERROR_DUMP_DIRECTORY)

@error.command(name = "list", short_help = "show current error dumps")
@click.pass_context
def list_errors(ctx: click.Context):
    """
    Show a list of current error dumps.
    """
    click.echo(formatting.DumpFileListFormatter().formatted(
            ctx.obj["errors"]))

@error.command(name = "clear", short_help = "delete all current error dumps")
@click.confirmation_option(prompt = "Delete all error dumps?")
@click.pass_context
def delete_errors(ctx: click.Context):
    """
    Delete all current error dumps.
    """
    for file in ctx.obj["errors"].files:
        os.unlink(os.path.join(ctx.obj["errors"].directory, file.name))

@error.command(name = "show", short_help = "delete all current error dumps")
@click.argument("number", type = int, default = 1)
@click.pass_context
def show_error(ctx: click.Context, number: int):
    try:
        err = ctx.obj["errors"].files[number-1]
    except IndexError:
        click.echo(f"No such error ({number}). Try running viewser system errors list.")
    else:
        with open(os.path.join(ctx.obj["errors"].directory,err.name)) as f:
            error_model = schema.Dump(**json.load(f))
        click.echo(formatting.DumpFileErrorFormatter().formatted(error_model))
