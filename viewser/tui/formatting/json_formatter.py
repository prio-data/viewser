import pydantic
from . import abc

class JsonFormatter(abc.Formatter[pydantic.BaseModel]):
    SECTIONS = []
    def formatted(self, model: pydantic.BaseModel) -> str:
        return model.json()
