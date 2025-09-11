from __future__ import annotations

from typing import Final, Optional

from src.sigaa_api.providers.provider import Provider
from src.sigaa_api.utils.parser import strip_html_bs4


class UFBAProvider(Provider):
    error_invalid_credentials: Final[str] = "SIGAA: Invalid credentials."
    KEY = "UFBA"
    HOST = "https://sigaa.ufba.br"

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

    def get_name(self) -> Optional[str]:
        with self._browser.page() as p:
            p.goto('/sigaa/portais/discente/discente.jsf')
            html = p.locator('#info-usuario > p.usuario > span').nth(0).inner_html()
            name = strip_html_bs4(html)
            return name

    def get_email(self) -> Optional[str]:
        with self._browser.page() as p:
            p.goto('/sigaa/portais/discente/discente.jsf')
            tbl = p.locator('#agenda-docente > table')
            if tbl.count() == 0:
                return None
            rows = tbl.nth(0).locator('tr')
            for i in range(rows.count()):
                row = rows.nth(i)
                tds = row.locator('td')
                if tds.count() < 2:
                    continue
                key = strip_html_bs4(tds.nth(0).inner_html() or '').strip().lower()
                if key in ('e-mail:', 'e-mail'):
                    value = strip_html_bs4(tds.nth(1).inner_html() or '')
                    if value:
                        return value
        return None

    def get_registration(self) -> Optional[str]:
        # Active student registration (Matrícula)
        with self._browser.page() as p:
            p.goto('/sigaa/portais/discente/discente.jsf')
            # Same selector used by account layer
            reg = str(p.locator('#agenda-docente > table > tbody > tr:nth-child(1) > td:nth-child(2)').nth(0).inner_html())
            reg = strip_html_bs4(reg or '')
            return reg or None

    def get_profile_picture_url(self) -> Optional[str]:
        with self._browser.page() as p:
            p.goto('/sigaa/portais/discente/discente.jsf')
            img = p.locator('#perfil-docente > div.pessoal-docente > div.foto > img')
            if img.count() == 0:
                return None
            src = img.nth(0).get_attribute('src')
            if not src:
                return None
            url = p.abs_url(src)
            return str(url) if url is not None else None

    def logoff(self) -> None:
        req = self.browser.request
        resp = req.get("/sigaa/logar.do?dispatch=logOff")
        if not (200 <= resp.status < 400):
            raise ValueError("SIGAA: Invalid status code in logoff page.")
