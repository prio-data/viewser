
from views_storage import key_value_store
from views_storage.backends import azure, sql
from views_storage.serializers import pickle
from viewser import settings
from viewser.storage.azure import connection_string
from viewser.storage import db, metadata_storage_serializer

class ModelObjectStorage(key_value_store.KeyValueStore):
    def __init__(self):
        super().__init__(
                backend = azure.AzureBlobStorageBackend(connection_string(
                    settings.config.get("AZURE_BLOB_STORAGE_ACCOUNT_NAME"),
                    settings.config.get("AZURE_BLOB_STORAGE_ACCOUNT_KEY"),
                    ), "models"),
                serializer = pickle.Pickle()
                )

class ModelMetadataStorage(key_value_store.KeyValueStore):
    def __init__(self):
        super().__init__(
                backend = sql.Sql(
                    engine = db.metadata_engine,
                    table_name = settings.config.get("MODEL_METADATA_DATABASE_TABLE"),
                    schema = settings.config.get("MODEL_METADATA_DATABASE_SCHEMA")),
                serializer = metadata_storage_serializer.MetadataStorageSerializer()
                )
