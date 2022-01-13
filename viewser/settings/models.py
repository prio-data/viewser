
import datetime
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base

metadata = sa.MetaData()
Base = declarative_base(metadata = metadata)

class Setting(Base):
    __tablename__ = "setting"
    key      = sa.Column(sa.String(), primary_key = True)
    value    = sa.Column(sa.String())
    modified = sa.Column(sa.DateTime(), default = datetime.datetime.now)
