
from typing import List
import pydantic

class Operation(pydantic.BaseModel):
    base: str
    path: str
    args: List[str]

class Queryset(pydantic.BaseModel):
    loa: str
    name: str
    theme: str
    operations: List[List[Operation]]
