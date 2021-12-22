
import click

@click.group(name = "logs", short_help = "commands for viewing and streaming logs")
def logs():
    pass


@logs.command(name = "list", short_help = "show available log streams")
def list_logs():
    pass

@logs.command(name = "stream", short_help = "open a log stream")
def stream_log():
    pass

@logs.command(name = "get", short_help = "download a log")
def get_log():
    pass
