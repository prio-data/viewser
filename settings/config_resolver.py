from typing import Callable, Dict, Union
from sqlalchemy.orm import Session
from . import models

class ConfigResolver():
    def __init__(self, sessionmaker: Callable[[], Session]):
        self._Session = sessionmaker

    def get_config(self, key: str) -> Union[str, int, float]:
        with self._Session() as session:
            return self._get(session, key)

    def set_config(self, key, value) -> None:
        with self._Session() as session:
            return self._set(session, key, value)

    def load(self, settings: Dict[str, Union[str, int, float]], overwrite: bool = False) -> None:
        with self._Session() as session:
            for key,value in settings.items():
                if self._get(session, key) is None or overwrite:
                    self._set(session, key, value)

    def _get(self, session: Session, key: str) -> Union[str, int, float]:
        return session.query(models.Setting).get(key)

    def _set(self, session: Session, key: str, value: Union[str, int, float]) -> None:
        setting = models.Setting(key = key, value = value)
        session.add(setting)
        session.commit()

