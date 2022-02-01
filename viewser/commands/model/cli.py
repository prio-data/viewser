import datetime
import pickle
import io
from typing import Dict, List
import click
from views_schema import models as schema
from views_storage import key_value_store
from viewser.storage import model_object
from viewser.tui.formatting.generic_models import ListModel
from viewser.tui.formatting.formatters import ListFormatter
from . import formatting

@click.group(name="model", short_help="management of model objects")
@click.pass_context
def cli(ctx: click.Context):
    ctx.obj["model_object_storage"] = model_object.ModelObjectStorage()
    ctx.obj["model_object_metadata_storage"] = model_object.ModelMetadataStorage()
    ctx.obj["detail_formatter"] = formatting.ModelMetadataFormatter()
    ctx.obj["table_formatter"] = ListFormatter()

@cli.command(name="list", short_help="show a list of model objects")
@click.pass_obj
def list_models(obj: Dict[str, key_value_store.KeyValueStore]):
    models = obj["model_object_storage"].list()
    click.echo(
            obj["table_formatter"].formatted(ListModel(values = models)))

@cli.command(name="download", short_help="download a model object to a file")
@click.argument("name", type=str)
@click.argument("file", type=click.File("wb"))
@click.pass_obj
def download_model(
    obj: Dict[str, key_value_store.KeyValueStore], name: str, file: io.BufferedWriter
):
    try:
        pickle.dump(obj["model_object_storage"].read(name), file)
    except KeyError:
        click.echo(f"No model named {name}")
    except ModuleNotFoundError as mnfe:
        click.echo(
            f"Oops! Seems like the store object uses a library that you don't have! "
            f'Please install the module "{mnfe.name}" and try again.'
        )


@cli.command(name="inspect", short_help="display metadata for a model object")
@click.argument("name", type=str)
@click.pass_obj
def inspect_model(obj: Dict[str, key_value_store.KeyValueStore], name: str):
    try:
        metadata = obj["model_object_metadata_storage"].read(name)
    except KeyError:
        try:
            try:
                obj["model_object_storage"].read(name)
            except ModuleNotFoundError:
                pass
        except KeyError:
            click.echo(f"No model named {name}")
        else:
            click.echo(
                f"Model {name} does not yet have any metadata. Annotate the model with viewser model annotate"
            )
    else:
        click.echo(obj["detail_formatter"].formatted(metadata))


@cli.command(name="annotate", short_help="add metadata for a model object")
@click.argument("model", type=str)
@click.option("-a", "--author", type=str, default = "")
@click.option("-q", "--queryset-name", type=str, default = "")
@click.option("-s", "--train-start", type=int, default = 0)
@click.option("-e", "--train-end", type=int, default = 0)
@click.option("-d", "--training-date", type=click.DateTime(), default=datetime.datetime.now())
@click.option("-s", "--step", type=int, multiple = True, default = [])
@click.pass_obj
def annotate_model(
    obj:           Dict[str, key_value_store.KeyValueStore],
    model:         str,
    author:        str,
    queryset_name: str,
    train_start:   int,
    train_end:     int,
    training_date: datetime.datetime,
    step:         List[int]
):
    md = schema.ModelMetadata(
        author=author,
        queryset_name=queryset_name,
        train_start=train_start,
        train_end=train_end,
        training_date=training_date,
        steps = list(step)
    )
    obj["model_object_metadata_storage"].write(model, md)
