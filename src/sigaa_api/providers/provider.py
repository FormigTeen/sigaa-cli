from abc import ABC, abstractmethod
from typing import ClassVar, Optional, List, Any
from src.sigaa_api.browser import SigaaBrowser
from src.sigaa_api.session import Session
from src.sigaa_api.models.active_course import ActiveCourse


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

    @abstractmethod
    def get_program(self) -> Optional[str]:
        ...

    @abstractmethod
    def get_registration(self) -> Optional[str]:
        ...

    @abstractmethod
    def get_profile_picture_url(self) -> Optional[str]:
        ...

    @abstractmethod
    def get_current_term(self) -> Optional[str]:
        ...

    @abstractmethod
    def get_programs(self) -> None:
        ...

    @abstractmethod
    def get_active_courses(self) -> List[ActiveCourse]:
        ...
