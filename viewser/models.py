
from typing import List
import pydantic

class Operation(pydantic.BaseModel):
    base: str
    path: str
    args: List[str]

class Database(Operation):
    base = "base"
    args:List[str] = ["values"]

class Transformed(Operation):
    base = "trf"

class Queryset(pydantic.BaseModel):
    loa: str
    name: str
    theme: str
    operations: List[List[Operation]]
