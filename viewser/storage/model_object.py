
from views_storage import key_value_store
from views_storage.backends import sftp
from views_storage.serializers import pickle, json
from viewser import settings

class ModelObjectStorage(key_value_store.KeyValueStore):
    def __init__(self):
        super().__init__(
                backend = sftp.Sftp(
                    host          = settings.config_get("MODEL_OBJECT_SFTP_HOSTNAME"),
                    port          = settings.config_get("MODEL_OBJECT_SFTP_PORT"),
                    user          = settings.config_get("MODEL_OBJECT_SFTP_USER"),
                    key_db_host   = settings.config_get("MODEL_OBJECT_KEY_DB_HOSTNAME"),
                    key_db_dbname = settings.config_get("MODEL_OBJECT_KEY_DB_DBNAME"),
                    folder        = "data/model_objects"),
                serializer = pickle.Pickle()
                )

    def list(self):
        raw = super().list()
        return raw.files

class ModelMetadataStorage(key_value_store.KeyValueStore):
    def __init__(self):
        super().__init__(
                backend = sftp.Sftp(
                    host          = settings.config_get("MODEL_OBJECT_SFTP_HOSTNAME"),
                    port          = settings.config_get("MODEL_OBJECT_SFTP_PORT"),
                    user          = settings.config_get("MODEL_OBJECT_SFTP_USER"),
                    key_db_host   = settings.config_get("MODEL_OBJECT_KEY_DB_HOSTNAME"),
                    key_db_dbname = settings.config_get("MODEL_OBJECT_KEY_DB_DBNAME"),
                    folder        = "data/metadata"),
                serializer = json.Json()
                )

    def list(self):
        raw = super().list()
        return raw.files
