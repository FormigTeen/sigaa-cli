from __future__ import annotations

from typing import Optional, cast

from .browser import BrowserConfig, SigaaBrowser
from src.sigaa_api.providers.ufba.provider import UFBAProvider
from .models.student import Student
from .parser import Parser
from .providers.provider import Provider
from .search.teacher import SigaaSearch
from .accounts.ufba import SigaaAccountUFBA
from .session import Session
from .types import Institution, LoginStatus

PROVIDERS = {
    UFBAProvider.KEY: UFBAProvider,
}


class Sigaa:
    def __init__(
        self,
        *,
        institution: str,
        headless: bool = True,
        parser: Optional[Parser] = None,
    ) -> None:
        if institution not in PROVIDERS:
            raise NotImplementedError(f"Institution {institution} not supported")
        self._provider_class = PROVIDERS[institution]

        self._browser = SigaaBrowser(BrowserConfig(base_url=self._provider_class.HOST, headless=headless))
        self._session = Session(institution=institution)
        self._parser = parser or Parser()

        # Apenas UFBA
        self._provider: Provider = PROVIDERS[institution](self._browser, self._session)
        self._student = Student(institution=institution)

    def login(self, username: str, password: str) -> bool:
        if self._session.login_status == LoginStatus.UNAUTHENTICATED:
            self._provider.login(username, password)
        self._session.login_status = LoginStatus.AUTHENTICATED
        return True

    def logoff(self) -> bool:
        if self._session.login_status == LoginStatus.AUTHENTICATED:
            self._provider.logoff()
            self._student = Student(institution=self._student.institution)
        self._session.login_status = LoginStatus.UNAUTHENTICATED
        return True

    def get_name(self) ->Optional[str]:
        if self._session.login_status == LoginStatus.UNAUTHENTICATED:
            raise ValueError("Not authenticated")
        if self._student.get_name():
            return self._student.get_name()
        self._student.set_name(self._provider.get_name())
        return self._student.get_name()

    def get_email(self):
        if self._session.login_status == LoginStatus.UNAUTHENTICATED:
            raise ValueError("Not authenticated")
        if self._student.get_email():
            return self._student.get_email()
        self._student.set_email(self._provider.get_email())
        return self._student.get_email()

    def close(self) -> None:
        self._browser.close()
