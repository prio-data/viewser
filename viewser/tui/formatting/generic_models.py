
from typing import List, Dict, Any
import pydantic

class ListModel(pydantic.BaseModel):
    values: List[str]

class DictModel(pydantic.BaseModel):
    values: Dict[str, Any]
