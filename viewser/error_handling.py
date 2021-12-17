import sys
import click
import shutil
from typing import List, TextIO
from abc import ABC, abstractmethod
import os
import datetime
from views_schema import viewser as schema

class ErrorDumpIO(ABC):

    @abstractmethod
    def write(self, dump: schema.Dump):
        pass

    def name(self, dump: schema.Dump, message: schema.Message) -> str:
        return f"viewser_{self.strftime(dump.timestamp)}_{dump.title}_{message.message_type.name}"

    def strftime(self, time: datetime.datetime):
        return time.strftime("%Y-%m-%d_%H:%M:%S")


class FileErrorHandler(ErrorDumpIO):

    def __init__(self, directory: str):
        self._directory = directory
        os.makedirs(self._directory, exist_ok = True)

    def write(self, dump: schema.Dump):
        for message in dump.messages:
            with open(self._path(dump, message), "w") as f:
                f.write(message.content)

    def _path(self, dump: schema.Dump, message: schema.Message):
        return os.path.join(self._directory, self.name(dump, message))


class StreamHandler(ErrorDumpIO):
    """
    StreamHandler
    ==================

    Reports back errors to the user via a stream (default sys.stdout).

    """
    def __init__(self, stream : TextIO = sys.stdout):
        self._buffer:   str = ""
        self._stream = stream
        self._hints:    List[schema.Message] = []
        self._messages: List[schema.Message] = []
        super().__init__()

    def write(self, dump: schema.Dump):
        for message in dump.messages:
            if message.message_type is schema.MessageType.HINT:
                self._hints.append(message)
            elif message.message_type is schema.MessageType.MESSAGE:
                self._messages.append(message)

        self._print()

    def _separator(self, char: str = "="):
        return char[0] * shutil.get_terminal_size()[0]

    def _print(self):
        self._stream.write(f"""

MESSAGES
~~~~~~~~
{self._separator()}
        """)

        for message in self._messages:
            self._stream.write(message.content)

        self._stream.write(f"""

HINTS
~~~~~
{self._separator()}
        """)

        for hint in self._hints:
            self._stream.write(hint.content)

        self._buffer = ""

class ErrorDumper():
    def __init__(self, writers: List[ErrorDumpIO]):
        self._writers = writers

    def dump(self, error_dump: schema.Dump):
        for writer in self._writers:
            writer.write(error_dump)
