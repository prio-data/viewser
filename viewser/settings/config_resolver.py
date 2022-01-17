from typing import Callable, Dict, Union, Any, Optional
import strconv
from sqlalchemy.orm import Session
from . import models, exceptions

class ConfigResolver():

    def __init__(self, sessionmaker: Callable[[], Session]):
        self._Session = sessionmaker

    def get(self, key: str, default: Optional[Any] = None) -> Union[str, int, float]:
        with self._Session() as session:
            try:
                assert (setting := self._get(session, key)) is not None
            except AssertionError:
                if default is None:
                    raise exceptions.ConfigurationError(f"Configuration setting {key} is not set")
                return default
            else:
                return strconv.convert(setting.value)

    def set(self, key, value) -> None:
        with self._Session() as session:
            return self._set(session, key, value)

    def unset(self, key) -> None:
        with self._Session() as session:
            return self._unset(session, key)

    def load(self, settings: Dict[str, Union[str, int, float]], overwrite: bool = False) -> None:
        with self._Session() as session:
            for key,value in settings.items():
                if not self._exists(session, key) or overwrite:
                    self._set(session, key, value)

    def list(self) -> Dict[str, Union[str, int, float]]:
        with self._Session() as session:
            settings = session.query(models.Setting).all()
            return {s.key: s.value for s in settings}

    def _get(self, session: Session, key: str) -> Union[str, int, float]:
        return session.query(models.Setting).get(key)

    def _exists(self, session: Session, key: str) -> bool:
        return session.query(models.Setting).get(key) is not None

    def _set(self, session: Session, key: str, value: Union[str, int, float]) -> None:
        if (existing := self._get(session,key)) is not None:
            existing.value = value
        else:
            setting = models.Setting(key = key, value = value)
            session.add(setting)
        session.commit()

    def _unset(self, session: Session, key: str) -> None:
        session.delete(session.query(models.Setting).get(key))
        session.commit()
