
import click

@click.group(name = "logs", short_help = "commands for viewing and streaming logs")
def cli():
    pass


@cli.command(name = "list", short_help = "show available log streams")
def list_logs():
    pass

@cli.command(name = "stream", short_help = "open a log stream")
def stream_log():
    pass

@cli.command(name = "get", short_help = "download a log")
def get_log():
    pass
