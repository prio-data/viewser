
from typing import List
import pydantic

class Operation(pydantic.BaseModel):
    namespace: str
    name: str
    arguments: List[str]

class Database(Operation):
    namespace = "base"
    arguments: List[str] = ["values"]

class Transformed(Operation):
    namespace = "trf"

class Queryset(pydantic.BaseModel):
    loa: str
    name: str
    themes: List[str]
    operations: List[List[Operation]]
