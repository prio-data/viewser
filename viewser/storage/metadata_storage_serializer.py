
from typing import Any, Union
from views_storage.serializers import serializer
from views_storage import types
from views_schema import models

def simplify_value(value: Any) -> Union[str, int, float, bool]:
    """
    simplify_value
    ==============

    Used to smooth over JSON serialization. Makes any non-simple value a string.

    """
    if isinstance(value, list):
        return [simplify_value(v) for v in value]
    elif isinstance(value, dict):
        return {simplify_value(k): simplify_value(v) for k,v in value.items()}
    else:
        return str(value) if type(value) not in {str, int, float, bool} else value

class MetadataStorageSerializer(serializer.Serializer[models.ModelMetadata, types.JsonSerializable]):
    """
    MetadataStorageSerializer
    =========================

    Class used to serialize and deserialize ModelMetadata models for storage
    using a views_storage Sql backend. Returns a dictionary representation of
    the model.

    """

    def serialize(self, obj: models.ModelMetadata)-> types.JsonSerializable:
        data = obj.dict()
        return {
                "author": obj.author,
                "values": {k: simplify_value(v) for k,v in data.items() if k not in {"run_id","author"}}
                }

    def deserialize(self, data: types.JsonSerializable) -> models.ModelMetadata:
        data = {**data, **data["values"]}
        del data["values"]
        return models.ModelMetadata(**data)
