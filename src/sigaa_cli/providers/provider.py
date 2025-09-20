from abc import ABC, abstractmethod
from shelve import Shelf
from typing import ClassVar, Optional, List, Any
from src.sigaa_cli.browser import SigaaBrowser
from src.sigaa_cli.models.course import RequestedCourse
from src.sigaa_cli.models.program import DetailedProgram
from tinydb import TinyDB
from src.sigaa_cli.models.section import ActiveSection, DetailedSection
from src.sigaa_cli.session import Session
from src.sigaa_cli.utils.cache import get_cache


class Provider(ABC):
    KEY: ClassVar[str]
    HOST: ClassVar[str]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if 'KEY' not in cls.__dict__:
            raise TypeError(f"{cls.__name__} deve definir o atributo de classe 'KEY'.")
        if not isinstance(cls.KEY, str) or not cls.KEY:
            raise TypeError("'KEY' deve ser uma string não vazia.")

    def __init__(self, browser: SigaaBrowser, session: Session) -> None:
        self._browser = browser
        self._session = session

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
    def get_programs(self) -> List[DetailedProgram]:
        ...

    def get_sections(self) -> List[DetailedSection]:
        ...

    @abstractmethod
    def get_active_courses(self) -> List[ActiveSection]:
        ...

    def get_host(self) -> str:
        return self.HOST

    def get_cache(self) -> Shelf[Any]:
        return get_cache(self.KEY)

    @abstractmethod
    def get_course(self, ref_id: str) -> RequestedCourse:
        ...
