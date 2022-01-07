
import pickle
import io
from typing import Dict
import click
from views_storage import key_value_store
from viewser.storage import model_object

@click.group(name = "model", short_help = "management of model objects")
@click.pass_context
def cli(ctx: click.Context):
    ctx.obj["model-object-storage"]          = model_object.ModelObjectStorage()
    ctx.obj["model-object-metadata-storage"] = model_object.ModelMetadataStorage()

@cli.command(name = "list", short_help = "show a list of model objects")
@click.pass_obj
def list_models(obj: Dict[str, key_value_store.KeyValueStore]):
    click.echo("\n".join(obj["model-object-storage"].list()))

@cli.command(name = "download", short_help = "download a model object to a file")
@click.argument("name", type = str)
@click.argument("file", type = click.File("wb"))
@click.pass_obj
def download_model(
        obj: Dict[str, key_value_store.KeyValueStore],
        name: str,
        file: io.BufferedWriter):
    try:
        pickle.dump(obj["model-object-storage"].read(name), file)
    except FileNotFoundError:
        click.echo(f"No model named {name}")

@cli.command(name = "inspect", short_help = "display metadata for a model object")
@click.argument("name", type = str)
@click.pass_obj
def inspect_model(obj: Dict[str, key_value_store.KeyValueStore], name: str):
    try:
        click.echo(obj["model-object-metadata-storage"].read(name))
    except FileNotFoundError:
        click.echo(f"No model named {name}")

