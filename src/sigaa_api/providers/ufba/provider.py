from __future__ import annotations

from typing import Final, Optional, List
import re

from src.sigaa_api.providers.provider import Provider
from src.sigaa_api.providers.ufba.utils.active_courses import get_table as get_active_courses_table
from src.sigaa_api.providers.ufba.utils.table_html import get_rows
from src.sigaa_api.utils.parser import strip_html_bs4
from src.sigaa_api.models.active_course import ActiveCourse


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
            p.safe_goto('/sigaa/portais/discente/discente.jsf')
            html = p.locator('#info-usuario > p.usuario > span').nth(0).inner_html()
            name = strip_html_bs4(html)
            return name

    def get_email(self) -> Optional[str]:
        with self._browser.page() as p:
            p.safe_goto('/sigaa/portais/discente/discente.jsf')
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

    def get_program(self) -> Optional[str]:
        with self._browser.page() as p:
            p.safe_goto('/sigaa/portais/discente/discente.jsf')
            # Same selector used by account layer
            reg = str(p.locator('#agenda-docente > table > tbody > tr:nth-child(2) > td:nth-child(2)').nth(0).inner_html())
            reg = strip_html_bs4(reg or '').replace('\n', '')
            reg = reg.strip()
            # Replace occurrences of 3+ consecutive whitespace chars with a single space
            reg = re.sub(r'\s{3,}', ' ', reg)
            return reg or None

    def get_registration(self) -> Optional[str]:
        # Active student registration (Matrícula)
        with self._browser.page() as p:
            p.safe_goto('/sigaa/portais/discente/discente.jsf')
            # Same selector used by account layer
            reg = str(p.locator('#agenda-docente > table > tbody > tr:nth-child(1) > td:nth-child(2)').nth(0).inner_html())
            reg = strip_html_bs4(reg or '')
            return reg or None

    def get_profile_picture_url(self) -> Optional[str]:
        with self._browser.page() as p:
            p.safe_goto('/sigaa/portais/discente/discente.jsf')
            img = p.locator('#perfil-docente > div.pessoal-docente > div.foto > img')
            if img.count() == 0:
                return None
            src = img.nth(0).get_attribute('src')
            if not src:
                return None
            url = p.abs_url(src)
            return str(url) if url is not None else None

    def get_current_term(self) -> Optional[str]:
        with self._browser.page() as p:
            p.safe_goto('/sigaa/portais/discente/discente.jsf')
            sel = '#turmas-portal > table:nth-child(3) > tbody > tr:nth-child(1) > td'
            loc = p.locator(sel)
            if loc.count() == 0:
                return None
            term_html = loc.nth(0).inner_html() or ''
            term = strip_html_bs4(term_html).strip()
            term = re.sub(r"\s+", " ", term)
            return term or None

    def get_active_courses(self) -> List[ActiveCourse]:
        courses: List[ActiveCourse] = []
        with self._browser.page() as p:
            p.goto('/sigaa/portais/discente/discente.jsf')
            tbl = get_active_courses_table(p)
            if tbl.count() == 0:
                return courses

            current_term = self.get_current_term() or ""

            rows = get_rows(tbl)
            rows_count = rows.count()
            i = 0

            while i < rows_count:
                row = rows.nth(i)
                tds = row.locator('td')
                if tds.count() < 3 or (tds.nth(0).get_attribute('colspan') is not None):
                    i += 1
                    continue

                # First column: course name (anchor inside td.descricao)
                name_node = row.locator('td.descricao a')

                if name_node.count() > 0:
                    name_html = name_node.nth(0).inner_html() or ''
                else:
                    name_html = tds.nth(0).inner_html() or ''
                name = strip_html_bs4(name_html).strip()

                # Second column: location
                location_html = tds.nth(1).inner_html() or ''
                location = strip_html_bs4(location_html).strip()

                # Third column: time code
                time_html = tds.nth(2).inner_html() or ''
                time_code = strip_html_bs4(time_html).strip()

                # Click the link to open the class page and extract code from #nomeTurma
                code_value = ""
                if name_node.count() > 0:
                    try:
                        name_node.nth(0).click()
                        p.wait_for_load_state('networkidle')
                        nome = p.locator('#nomeTurma')
                        if nome.count() > 0:
                            code_html = nome.nth(0).inner_html() or ''
                            code_value = strip_html_bs4(code_html).strip()
                    except Exception:
                        code_value = ""
                    finally:
                        # Return to previous page using history
                        p.go_back()
                        p.wait_for_selector('#turmas-portal > table:nth-child(3)')

                courses.append(
                    ActiveCourse(
                        code=code_value,
                        name=name,
                        location=location,
                        time_code=time_code,
                        term=current_term,
                    )
                )

                i += 1

        return courses

    def logoff(self) -> None:
        req = self.browser.request
        resp = req.get("/sigaa/logar.do?dispatch=logOff")
        if not (200 <= resp.status < 400):
            raise ValueError("SIGAA: Invalid status code in logoff page.")
