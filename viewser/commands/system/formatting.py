
import tabulate
from views_schema import viewser as schema
from viewser.tui.formatting import abc
from . import models

class ErrorDumpFilesTable(abc.Section[models.ErrorDumpFiles]):
    TITLE = "Error dumps"

    def compile_output(self, model: models.ErrorDumpFiles):
        return tabulate.tabulate(
                [(i+1, f.name, str(f.size)+" bytes") for i, f in enumerate(model.files)],
                headers = ("filename", "size"),
                tablefmt = "pipe")

class DumpHeader(abc.Section[schema.Dump]):
    TITLE = "Error dump"

    def compile_output(self, model: schema.Dump)-> str:
        return (f"\"{model.title}\"\n"
            f"This error was posted at {model.timestamp} by {model.username}")

class MessagesSummary(abc.Section[schema.Dump]):
    TITLE = "Messages"

    def compile_output(self, model: schema.Dump)-> str:
        for message in model.messages:
            msg = message.message_type.name
            if message.message_type is schema.MessageType.DUMP:
                msg += f"\nSize: {len(message.content)}"
            else:
                msg += f"\n{message.content}"
        return msg

class DumpFileListFormatter(abc.Formatter[models.ErrorDumpFiles]):
    SECTIONS = [
            ErrorDumpFilesTable
        ]

class DumpFileErrorFormatter(abc.Formatter[schema.Dump]):
    SECTIONS = [
            DumpHeader,
            MessagesSummary,
        ]
