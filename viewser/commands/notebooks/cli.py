from typing import Optional
from toolz.functoolz import curry
from pymonad.maybe import Just, Nothing
import click
from viewser.error_handling import exceptions
from viewser import settings
from . import operations

@click.group(name="notebooks", short_help="run ipython notebooks")
def cli():
    pass

@cli.command(name="run", short_help="start the viewserspace ipython notebook server")
@click.option("-r","--requirements-file", type = str, default = None, help = "Optional requirements file")
@click.option("-w","--work-dir", type = str, default = ".", help = "Directory to mount")
@click.option("-v","--use-version", type = str, default="latest", help="Image version to use")
@click.option("--browser/--no-browser", type = bool, default=True, help="Automatically open a browser window")
@click.option("--pull/--no-pull", type = bool, default=True, help="Check for environment updates")
def run_viewserspace(
        use_version: str,
        work_dir: str,
        browser: bool,
        pull: bool,
        requirements_file: Optional[str],
        ):

    requirements_file = Just(requirements_file) if requirements_file else Nothing
    port = operations.seek_port(operations.START_PORT)

    if not port:
        click.echo("No available ports")
    else:
        (operations.notebook_image(
                settings.config_get("NOTEBOOK_SERVER_IMAGE_REGISTRY"),
                settings.config_get("NOTEBOOK_SERVER_IMAGE_REPOSITORY"),
                use_version,
                pull)
            .then(curry(operations.run_notebook_server, port, work_dir, requirements_file))
            .either(
                curry(exceptions.exception_raiser,exceptions.ViewserspaceError),
                curry(operations.watch, browser, click.echo))
            )
