import json
from typing import Any, Dict
import sys
import io
import click
from viewser import settings
from viewser.tui.formatting.formatters import DictFormatter
from viewser.tui.formatting.generic_models import DictModel

@click.group(name="config", short_help="configure viewser")
@click.pass_obj
def cli(obj: Dict[str,Any]):
    """
    Configure viewser
    """
    obj["table_formatter"] = DictFormatter()

@cli.command(name="interactive", short_help="interactively configure viewser")
def config_interactive():
    """
    Interactively configure viewser (useful for first-time config)
    """
    settings.configure_interactively()
    click.echo("All done!")

@cli.command(name="set", short_help="set a configuration value")
@click.argument("name", type=str)
@click.argument("value", type=str, default=1)
@click.option("--override/--no-override",default=True)
def config_set(name: str, value: str, override: bool): # pylint: disable=redefined-builtin
    """
    Set a configuration value.
    """
    overrides = True
    try:
        settings.config.get(name)
    except settings.exceptions.ConfigurationError:
        overrides = False

    if not override and overrides:
        click.echo(f"Setting {name} already set, override not specified (see --help)")
        return

    settings.config.set(name,value)
    click.echo(f"{name}: {value}")

@cli.command(name="get", short_help="get a configuration value")
@click.argument("name", type=str)
def config_get(name: str):
    """
    Get a configuration value.
    """
    value = settings.config.get(name)
    if value:
        click.echo(f"{name}: {value}")
    else:
        click.echo(f"{name} not set")
        sys.exit(1)

@cli.command(name="reset", short_help="reset default config values")
@click.confirmation_option(prompt="Reset config?")
def config_reset():
    """
    Reset config, writing default values over current values.
    """
    settings.config.load(settings.static.DEFAULT_SETTINGS, overwrite = True)
    click.echo("Config file reset")

@cli.command(name="list", short_help="show all configuration settings")
@click.pass_obj
def config_list(obj: Dict[str, Any]):
    """
    Show all current configuration values
    """
    click.echo(obj["table_formatter"].formatted(DictModel(values = settings.config.list().items())))

@cli.command(name="unset", short_help="unset a configuration value")
@click.confirmation_option(prompt="Unset config key?")
@click.argument("name", type=str)
def config_unset(name: str):
    """
    Unset a configuration value, removing its entry from the config file.
    """
    current_value = settings.config.get(name)
    settings.config.unset(name)
    click.echo(f"Unset {name} (was {current_value})")

@cli.command(name = "dump", short_help = "dump current config as JSON")
def config_dump():
    click.echo(json.dumps(settings.config.list()))

@cli.command(name = "load", short_help = "load configuration from a JSON file")
@click.confirmation_option(prompt="Load config file? (overwrites current config values)")
@click.argument("file", type = click.File("r"))
def config_load(file: io.BufferedReader):
    settings.config.load(json.load(file), overwrite = True)
