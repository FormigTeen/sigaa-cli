from __future__ import annotations

from typing import Optional, cast, List

from .browser import BrowserConfig, SigaaBrowser
from src.sigaa_api.providers.ufba.provider import UFBAProvider
from .models.account import Account
from .parser import Parser
from .providers.provider import Provider
from .search.teacher import SigaaSearch
from .accounts.ufba import SigaaAccountUFBA
from .session import Session
from .types import Institution, LoginStatus
from .models.active_course import ActiveCourse
from .utils.config import get_config_if_none, USER_KEY, PASSWORD_KEY, DEFAULT_PROVIDER_KEY

PROVIDERS = {
    UFBAProvider.KEY: UFBAProvider,
}


class Sigaa:
    def __init__(
        self,
        *,
        institution: Optional[str] = None,
        headless: bool = True,
        parser: Optional[Parser] = None,
    ) -> None:
        final_institution = get_config_if_none(DEFAULT_PROVIDER_KEY, institution, "UFBA")
        if final_institution not in PROVIDERS:
            raise NotImplementedError(f"Institution {final_institution} not supported")
        self._provider_class = PROVIDERS[final_institution]

        self._browser = SigaaBrowser(BrowserConfig(base_url=self._provider_class.HOST, headless=headless))
        self._session = Session(institution=institution)
        self._parser = parser or Parser()

        # Apenas UFBA
        self._provider: Provider = self._provider_class(self._browser, self._session)
        self._account: Optional[Account] = None
        self._active_courses: Optional[List[ActiveCourse]] = None

    def login(self, username: Optional[str] = None, password: Optional[str] = None) -> bool:
        if self._session.login_status == LoginStatus.UNAUTHENTICATED:
            self._provider.login(get_config_if_none(USER_KEY, username), get_config_if_none(PASSWORD_KEY, password))
        self._session.login_status = LoginStatus.AUTHENTICATED
        return True

    def logoff(self) -> bool:
        if self._session.login_status == LoginStatus.AUTHENTICATED:
            self._provider.logoff()
            self._account = None
        self._session.login_status = LoginStatus.UNAUTHENTICATED
        return True

    def get_account(self) -> Account:
        if self._session.login_status == LoginStatus.UNAUTHENTICATED:
            raise ValueError("Not authenticated")
        if self._account is not None:
            return self._account
        return Account(
            provider=self._provider.KEY,
            registration=self._provider.get_registration(),
            name=self._provider.get_name(),
            email=self._provider.get_email(),
            profile_picture_url=self._provider.get_profile_picture_url(),
            program=self._provider.get_program(),
        )

    def close(self) -> None:
        self._browser.close()

    def get_active_courses(self) -> List[ActiveCourse]:
        if self._session.login_status == LoginStatus.UNAUTHENTICATED:
            raise ValueError("Not authenticated")
        if self._active_courses is not None:
            return self._active_courses
        courses = self._provider.get_active_courses()
        self._active_courses = courses
        return courses

    def get_programs(self) -> None:
        if self._session.login_status == LoginStatus.UNAUTHENTICATED:
            raise ValueError("Not authenticated")
        self._provider.get_programs()

    def get_sections(self) -> None:
        if self._session.login_status == LoginStatus.UNAUTHENTICATED:
            raise ValueError("Not authenticated")
        self._provider.get_sections()
