
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from . import static

engine = sa.create_engine(f"sqlite:///{static.CONFIG_DB_FILE}")
Session = sessionmaker(engine)
