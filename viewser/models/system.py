
import os
from typing import List
from pydantic import BaseModel

class ErrorDumpFile(BaseModel):
    name: str
    size: int

class ErrorDumpFiles(BaseModel):
    directory: str
    files:     List[ErrorDumpFile]

    @classmethod
    def from_dir(cls: "ErrorDumpFiles", dir: str):
        size = lambda f: os.path.getsize(os.path.join(dir, f))
        files = [ErrorDumpFile(name = f, size = size(f)) for f in os.listdir(dir)]
        return cls(directory = dir, files = files)
