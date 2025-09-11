from abc import ABC, abstractmethod
from typing import ClassVar, Optional

from src.sigaa_api.browser import SigaaBrowser
from src.sigaa_api.session import Session


class Provider(ABC):
    KEY: ClassVar[str]
    HOST: ClassVar[str]

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if 'KEY' not in cls.__dict__:
            raise TypeError(f"{cls.__name__} deve definir o atributo de classe 'KEY'.")
        if not isinstance(cls.KEY, str) or not cls.KEY:
            raise TypeError("'KEY' deve ser uma string não vazia.")

    def __init__(self, browser: SigaaBrowser, session: Session) -> None:
        self._browser = browser
        self._session = session

    @abstractmethod
    def logoff(self) -> None:
        ...

    @abstractmethod
    def login(self, username: str, password: str) -> None:
        ...

    @abstractmethod
    def get_email(self) -> Optional[str]:
        ...

    @abstractmethod
    def get_name(self) -> Optional[str]:
        ...