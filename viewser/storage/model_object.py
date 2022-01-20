
from views_storage import key_value_store
from views_storage.backends import azure
from views_storage.serializers import pickle, json
from viewser import settings
from viewser.storage.azure import connection_string

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
                backend = azure.AzureBlobStorageBackend(connection_string(
                    settings.config.get("AZURE_BLOB_STORAGE_ACCOUNT_NAME"),
                    settings.config.get("AZURE_BLOB_STORAGE_ACCOUNT_KEY"),
                    ), "metadata"),
                serializer = json.Json()
                )
