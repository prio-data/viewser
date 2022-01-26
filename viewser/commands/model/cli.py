
import datetime
import pickle
import io
from typing import Dict
import click
from views_schema import models as schema
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
    except KeyError:
        click.echo(f"No model named {name}")
    except ModuleNotFoundError as mnfe:
        click.echo(f"Oops! Seems like the store object uses a library that you don't have! "
                f"Please install the module \"{mnfe.name}\" and try again.")

@cli.command(name = "inspect", short_help = "display metadata for a model object")
@click.argument("name", type = str)
@click.pass_obj
def inspect_model(obj: Dict[str, key_value_store.KeyValueStore], name: str):
    try:
        metadata = obj["model-object-metadata-storage"].read(name)
    except KeyError:
        try:
            try:
                obj["model-object-storage"].read(name)
            except ModuleNotFoundError:
                pass
        except KeyError:
            click.echo(f"No model named {name}")
        else:
            click.echo(f"Model {name} does not yet have any metadata. Annotate the model with viewser model annotate")
    else:
        click.echo(metadata)

@cli.command(name = "annotate", short_help = "add metadata for a model object")
@click.argument("model", type = str)
@click.option("-a","--author", type = str)
@click.option("-r","--run-id", type = str)
@click.option("-q","--queryset-name", type = str)
@click.option("-s","--train-start", type = int)
@click.option("-e","--train-end", type = int)
@click.option("-dt","--training-date", type = click.DateTime(), default = datetime.datetime.now())
@click.pass_obj
def annotate_model(obj: Dict[str, key_value_store.KeyValueStore], model, author, run_id, queryset_name, train_start, train_end, training_date):
    md = schema.ModelMetadata(
            author        = author,
            run_id        = run_id,
            queryset_name = queryset_name,
            train_start   = train_start,
            train_end     = train_end,
            training_date = training_date
            )
    obj["model-object-metadata-storage"].write(model, md)


