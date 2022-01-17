
import os

CONFIG_DIR = os.path.abspath(os.path.expanduser("~/.views"))
CONFIG_DB_FILE = os.path.join(CONFIG_DIR, "settings.sqlite")

DEFAULT_SETTINGS = {
        "RETRY_FREQUENCY":                  5,
        "LOG_LEVEL":                        "INFO",
        "HANDSHAKE_PATH":                   "",
        "REPO_URL":                         "https://www.github.com/prio-data/viewser",
        "LATEST_KNOWN_VERSION":             "0.0.0",
        "NOTEBOOK_SERVER_IMAGE_REPOSITORY": "prio-data/viewserspace",
        "NOTEBOOK_SERVER_IMAGE_REGISTRY":   "viewsregistry.azurecr.io",
        "ERROR_DUMP_DIRECTORY":             os.path.join(CONFIG_DIR, "dumps"),
        "MODEL_OBJECT_SFTP_USER":           "predictions",
        "MODEL_OBJECT_SFTP_PORT":           22222,
        "MODEL_OBJECT_SFTP_HOSTNAME":       "hermes",
        "MODEL_OBJECT_KEY_DB_HOSTNAME":     "janus",
        "MODEL_OBJECT_KEY_DB_DBNAME":       "pred3_certs",
        "QUERYSET_MAX_RETRIES":             500,
        "QUERYSET_REMOTE_PATH":             "querysets",
    }

REQUIRED_SETTINGS = (
            "REMOTE_URL",
        )
