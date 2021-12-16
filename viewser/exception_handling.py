import json
from typing import List
from abc import ABC, abstractmethod
import os
import datetime
from views_schema import viewser as schema

class ErrorDumpIO(ABC):

    def read(self, name: str)-> schema.Dump:
        return schema.Dump(**json.loads(self._read(name)))

    def write(self, dump: schema.Dump):
        self._write(f"{self.name(dump)}", dump.json())

    def name(self, dump: schema.Dump)-> str:
        return f"{self.strftime(dump.timestamp)}_{dump.title}"

    def strftime(self, time: datetime.datetime):
        return time.stftime("%Y-%m-%d_%H:%M:%S")

    @abstractmethod
    def _read(self, name: str):
        pass

    @abstractmethod
    def _write(self, name: str, content: str):
        pass

class FileErrorHandler(ErrorDumpIO):
    def __init__(self, directory: str):
        self._directory = directory

    def _write(self, name: str, content: str):
        with open(os.path.join(self._directory, name), "w") as f:
            f.write(content)

    def _read(self, name: str):
        with open(os.path.join(self._directory, name)) as f:
            return f.read()

class ErrorDumper():
    def __init__(self, writers: List[ErrorDumpIO]):
        self._writers = writers

    def dump(self, error_dump: schema.Dump):
        for writer in self._writers:
            writer.write(error_dump)
