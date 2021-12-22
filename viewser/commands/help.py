from importlib.metadata import version
import click
from viewser.operations import help as help_operations
from viewser import settings

@click.group(name="help", short_help="commands for finding documentation")
def help():
    """
    Commands related to finding documentation.
    """

@help.command(name = "wiki")
def wiki():
    """
    Open the viewser wiki in a new browser window, which contains all you need
    to know about using viewser.
    """
    help_operations.open_browser(settings.config_get("REPO_URL"),"wiki")

@help.command(name = "issue")
def issue():
    """
    Opens the viewser "new issue" page in a new browser window.
    """
    help_operations.open_browser(
            settings.config_get("REPO_URL"),
            "issue","new",
            body=f"My viewser version is {version('viewser')}"
        )

