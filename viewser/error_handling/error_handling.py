import sys
from typing import List, TextIO
from abc import ABC, abstractmethod
import os
import datetime
from views_schema import viewser as schema
from viewser.tui.formatting import errors as error_formatting
from pymonad.maybe import Nothing

class ErrorDumpIO(ABC):
    """
    ErrorDumpIO
    ===========

    Abstract class for error handling, outputting error content (schema.Dump)
    to some output.
    """

    @abstractmethod
    def write(self, dump: schema.Dump):
        pass

    def name(self, dump: schema.Dump, message: schema.Message) -> str:
        return f"viewser_{self.strftime(dump.timestamp)}_{dump.title}_{message.message_type.name}"

    def strftime(self, time: datetime.datetime):
        return time.strftime("%Y-%m-%d_%H:%M:%S")


class FileErrorHandler(ErrorDumpIO):
    """
    FileErrorHandler
    ================

    Dumps error contents to file.
    """

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
    def __init__(self, stream: TextIO = sys.stdout):
        self._stream: TextIO                 = stream

        self._buffer: str                    = ""
        self._hints: List[schema.Message]    = []
        self._messages: List[schema.Message] = []

        self._formatter                      = error_formatting.ErrorFormatter()

        super().__init__()

    def write(self, dump: schema.Dump):
        self._stream.write(self._formatter.formatted(dump))

class ErrorDumper():
    def __init__(self, writers: List[ErrorDumpIO]):
        self._writers = writers

    def dump(self, error_dump: schema.Dump) -> Nothing:
        for writer in self._writers:
            writer.write(error_dump)
        return Nothing
