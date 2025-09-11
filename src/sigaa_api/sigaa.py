from __future__ import annotations

from typing import Optional

from .browser import BrowserConfig, SigaaBrowser
from .login import SigaaLoginUFBA
from .parser import Parser
from .search.teacher import SigaaSearch
from .accounts.ufba import SigaaAccountUFBA
from .session import Session
from .types import Institution


class Sigaa:
    def __init__(
        self,
        *,
        institution: Institution = Institution.UFBA,
        url: str,
        headless: bool = True,
        parser: Optional[Parser] = None,
    ) -> None:
        self._browser = SigaaBrowser(BrowserConfig(base_url=url, headless=headless))
        self._session = Session(institution=institution)
        self._parser = parser or Parser()

        # Apenas UFBA
        if institution != Institution.UFBA:
            raise NotImplementedError(f"Institution {institution} not supported (only UFBA)")
        self._login = SigaaLoginUFBA(self._browser, self._session)

    def login(self, username: str, password: str) -> SigaaAccountUFBA:
        self._login.login(username, password)
        return SigaaAccountUFBA(self._browser, self._parser, self._session)

    @property
    def search(self) -> SigaaSearch:
        return SigaaSearch(self._browser, self._parser)

    def close(self) -> None:
        self._browser.close()
