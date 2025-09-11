from __future__ import annotations

from typing import Optional, cast

from .browser import BrowserConfig, SigaaBrowser
from src.sigaa_api.providers.ufba.provider import UFBAProvider
from .models.account import Account
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
        self._account: Optional[Account] = None

    def login(self, username: str, password: str) -> bool:
        if self._session.login_status == LoginStatus.UNAUTHENTICATED:
            self._provider.login(username, password)
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
        )

    def close(self) -> None:
        self._browser.close()
