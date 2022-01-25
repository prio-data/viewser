
from sqlalchemy import create_engine
from viewser import settings

metadata_engine = create_engine((
    "postgresql://"
    f"{settings.config.get('MODEL_METADATA_DATABASE_HOSTNAME')}"
    f"/{settings.config.get('MODEL_METADATA_DATABASE_NAME')}"
    ))
