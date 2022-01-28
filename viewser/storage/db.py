
from psycopg2 import connect, OperationalError
from sqlalchemy import create_engine
from viewser import settings

def get_metadata_con():
    parameters = {
            "host":    settings.config.get("MODEL_METADATA_DATABASE_HOSTNAME","0.0.0.0"),
            "port":    settings.config.get("MODEL_METADATA_DATABASE_PORT", 5432),
            "dbname":  settings.config.get("MODEL_METADATA_DATABASE_NAME", "postgres"),
            "sslmode": settings.config.get("MODEL_METADATA_DATABASE_SSLMODE", "require"),
        }

    if user := settings.config.get("MODEL_METADATA_DATABASE_USER", ""):
        parameters["user"] = user
    else:
        # Try to infer
        parameters["user"] = "postgres"

    if password := settings.config.get("MODEL_METADATA_DATABASE_PASSWORD", ""):
        parameters["password"] = password

    try:
        return connect(" ".join([str(k)+"="+str(v) for k,v in parameters.items()]))
    except OperationalError:
        raise ValueError((
            "Something went wrong when connecting to the metadata database. Make sure that the following config values are set: "
            "MODEL_METADATA_DATABASE_HOST, "
            "MODEL_METADATA_DATABASE_NAME, "
            "MODEL_METADATA_DATABASE_USER"
        ))

metadata_engine = create_engine("postgresql://", creator = get_metadata_con)
