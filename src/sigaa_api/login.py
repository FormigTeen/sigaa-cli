from __future__ import annotations

from typing import Final

from .browser import SigaaBrowser
from .session import Session
from .types import LoginStatus


class SigaaLoginUFBA:
    error_invalid_credentials: Final[str] = "SIGAA: Invalid credentials."

    def __init__(self, browser: SigaaBrowser, session: Session) -> None:
        self._browser = browser
        self._session = session

    def login(self, username: str, password: str) -> None:
        req = self._browser.request
        # Carrega página de login para iniciar sessão
        req.get("/sigaa/logar.do?dispatch=logOn")
        resp = req.post("/sigaa/logar.do?dispatch=logOn", data={
            "user.login": username,
            "user.senha": password,
            "entrar": "Entrar",
        })
        html = resp.body().decode(errors="ignore")
        if ("Usuário e/ou senha inválidos" in html) or ("/sigaa/logar.do" in html and "loginForm" in html):
            raise ValueError(self.error_invalid_credentials)
        probe = req.get("/sigaa/portais/discente/discente.jsf")
        if probe.status in (401, 403):
            raise ValueError(self.error_invalid_credentials)
        self._session.login_status = LoginStatus.AUTHENTICATED
