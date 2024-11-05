
import datetime
import io
import pandas as pd
import requests
from typing import Optional, Dict, Any

import click
from viewser import settings


@click.group(name="queryset", short_help="queryset_operations related to querysets")
@click.pass_obj
def cli(ctx_obj: Dict[str, Any]):
    """
    queryset-related cli functions
    """


@cli.command(name="list", short_help="show a list of available querysets")
def queryset_list():
    """
    Show a list of available querysets.
    """

    response = requests.get(url=f'{settings.REMOTE_URL}/querysets/querysets')

    querysets = response.json()['querysets']

    response_df = pd.DataFrame({'queryset_name': querysets})

    print(response_df.to_string())


@cli.command(name="show", short_help="show code for a queryset")
@click.argument("name", type=str)
def queryset_show(name: str):
    """
    Show detailed information about a queryset
    """

    response = requests.get(url=f'{settings.REMOTE_URL}/querysets//querysets/{name}')

    json_ = response.json()

    print(qs_json_to_code(json_))


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


def qs_json_to_code(json_):

    """
    Hideous piece of code which converts the json representation of a Queryset into a runnable code fragment
    """

    allowed_fields = ['name', 'loa', 'description', 'themes', 'operations']
    allowed_namespaces = ['base', 'trf']

    for key in json_.keys():
        if key not in allowed_fields:
            raise RuntimeError(f'Queryset json contains unrecognised field: {key}')

    lines = []

    tab = '    '

    line = f"(Queryset('{json_['name']}','{json_['loa']}')"

    lines.append(line)

    ops = json_['operations']

    for column in ops:
        for op in column[::-1]:
            if op['namespace'] not in allowed_namespaces:
                raise RuntimeError(f"Queryset operation contains unrecognised namespace: {op['namespace']}")
            if op['namespace'] == 'base':
                for op2 in column:
                    if op2['namespace'] == 'trf' and op2['name'] == 'util.rename':
                        rename = op2['arguments'][0]
                loa, name = op['name'].split('.')

                line = f"{tab}.with_column(Column('{rename}', from_loa='{loa}', from_column='{name}')"
                lines.append(line)
                if op['arguments'][0] != 'values':
                    arg = op['arguments'][0]
                    line = f"{tab}{tab}.aggregate('{arg}')"
                    lines.append(line)

            if op['namespace'] == 'trf' and op['name'] != 'util.rename':
                args = ','.join(op['arguments'])
                line = f"{tab}{tab}.transform.{op['name']}({args})"
                lines.append(line)

        line = f"{tab}{tab})"
        lines.append(line)
        line = f""
        lines.append(line)

    if len(json_['themes']) > 0:
        line = f"{tab}.with_theme('{json_['themes'][0]}')"
        lines.append(line)

    if json_['description'] is not None:
        line = f'{tab}.describe("""{json_["description"]}""")'
        lines.append(line)

    line = f"{tab})"
    lines.append(line)

    qs_code = '\n'.join(lines)

    return qs_code
