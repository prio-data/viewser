from importlib.metadata import version
import click
from viewser import settings
from . import operations

@click.group(name="help", short_help="commands for finding documentation")
def cli():
    """
    Commands related to finding documentation.
    """

@cli.command(name = "wiki")
def wiki():
    """
    Open the viewser wiki in a new browser window, which contains all you need
    to know about using viewser.
    """
    operations.open_browser(settings.config_get("REPO_URL"),"wiki")

@cli.command(name = "issue")
def issue():
    """
    Opens the viewser "new issue" page in a new browser window.
    """
    operations.open_browser(
            settings.config_get("REPO_URL"),
            "issue","new",
            body=f"My viewser version is {version('viewser')}"
        )
