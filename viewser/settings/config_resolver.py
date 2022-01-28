from typing import Callable, Dict, Union, Any, Optional
import strconv
from sqlalchemy.orm import Session
from . import models, exceptions, validation

class ConfigResolver():
    """
    ConfigResolver
    ==============

    parameters:
        sessionmaker (Callable[[], sqlalchemy.orm.Session])
        validate_key (Callable[[str], str]) = viewser.settings.validation.validate_key

    A class for managing configuration settings via a database table of
    settings. The validate_key function can be used to make sure that keys
    follow a certain format.
    """
    def __init__(self,
            sessionmaker: Callable[[], Session],
            validate_key: Callable[[str],str] = validation.validate_key):

        self._Session = sessionmaker
        self._validate_key = validate_key

    def get(self, key: str, default: Optional[Any] = None) -> Union[str, int, float]:
        """
        get
        ===

        parameters:
            key (str): Name of the configuration setting to get
            default (Optional[Any]): Default if setting is not set
        returns:
            Union[str, int, float]

        Get a configuration setting, optionally with a default. If neither the
        setting, nor a default is set, raises viewser.exceptions.ConfigurationError.
        """
        with self._Session() as session:
            try:
                assert (setting := self._get(session, key)) is not None
            except AssertionError:
                if default is None:
                    raise exceptions.ConfigurationError(f"Configuration setting {key} is not set")
                return default
            else:
                return strconv.convert(setting.value)

    def set(self, key: str, value: Union[str, int, float]) -> None:
        """
        set
        ===

        parameters:
            key (str)
            value (Union[str, int, float])

        Set the configuration setting key to value.

        """
        with self._Session() as session:
            return self._set(session, key, value)

    def unset(self, key: str) -> None:
        """
        unset
        =====

        parameters:
            key (str)

        Delete the configuration setting key. Note: Not reversible!
        """
        with self._Session() as session:
            return self._unset(session, key)

    def load(self, settings: Dict[str, Union[str, int, float]], overwrite: bool = False) -> None:
        """
        load
        ====

        parameters:
            settings (Dict[str, Union[str, int, float]])
            overwrite (bool)

        Set all configuration settings from a dictionary. Overwrites existing
        values if overwrite is True.
        """
        with self._Session() as session:
            for key,value in settings.items():
                if not self._exists(session, key) or overwrite:
                    self._set(session, key, value)

    def list(self) -> Dict[str, Union[str, int, float]]:
        """
        list
        ====

        returns:
            Dict[str, Union[str, int, float]]

        Get currently set configuration values
        """
        with self._Session() as session:
            settings = session.query(models.Setting).all()
            return {s.key: s.value for s in settings}

    def _get(self, session: Session, key: str) -> Union[str, int, float]:
        key = self._validate_key(key)

        return session.query(models.Setting).get(key)

    def _exists(self, session: Session, key: str) -> bool:
        key = self._validate_key(key)

        return session.query(models.Setting).get(key) is not None

    def _set(self, session: Session, key: str, value: Union[str, int, float]) -> None:
        key = self._validate_key(key)

        if (existing := self._get(session,key)) is not None:
            existing.value = value
        else:
            setting = models.Setting(key = key, value = value)
            session.add(setting)
        session.commit()

    def _unset(self, session: Session, key: str) -> None:
        key = self._validate_key(key)

        session.delete(session.query(models.Setting).get(key))
        session.commit()
