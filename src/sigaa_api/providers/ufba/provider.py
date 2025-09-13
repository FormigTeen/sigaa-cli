from __future__ import annotations

from typing import Final, Optional, List
import re

from src.sigaa_api.providers.provider import Provider
from src.sigaa_api.providers.ufba.utils.active_courses import get_table as get_active_courses_table, \
    is_valid_active_course_line, get_active_course, to_detail_page_and_extract
from src.sigaa_api.providers.ufba.utils.detail_program import extract_detail_program
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

    def get_program(self) -> Optional[str]:
        with self._browser.page() as p:
            p.goto('/sigaa/portais/discente/discente.jsf')
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

    def get_current_term(self) -> Optional[str]:
        with self._browser.page() as p:
            p.goto('/sigaa/portais/discente/discente.jsf')
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
            rows = list(filter(is_valid_active_course_line, rows))

            for row in rows:

                name, location, time_code = get_active_course(row)
                code_value, count, *extra = to_detail_page_and_extract(p, row)

                courses.append(
                    ActiveCourse(
                        code=code_value,
                        name=name,
                        location=location,
                        time_code=time_code,
                        term=current_term,
                    )
                )


        return courses

    def get_programs(self) -> None:
        with self._browser.page() as page:
            page.goto('/sigaa/geral/estrutura_curricular/busca_geral.jsf')
            page.wait_for_selector('#busca\\:curso')

            # Itera sobre os cursos, ignorando a primeira opção (placeholder)
            course_options = page.locator('#busca\\:curso > option')
            total_courses = course_options.count()
            course_options = [course_options.nth(index) for index in range(1, total_courses)]
            course_option_values = [option.get_attribute('value') for option in course_options]
            course_option_values = [value for value in course_option_values if value]

            for course_value in course_option_values:
                # Seleciona o curso para carregar as matrizes e coletar todos os valores
                page.locator('#busca\\:curso').nth(0).select_option(course_value)
                page.wait_for_selector('#busca\\:matriz')

                matriz_options = page.locator('#busca\\:matriz > option')
                total_matrizes = matriz_options.count()

                matriz_options = [matriz_options.nth(index) for index in range(1, total_matrizes)]
                matriz_values = [option.get_attribute('value') for option in matriz_options]

                for matriz_value in matriz_values:
                    page.locator('#busca\\:curso').nth(0).select_option(course_value)
                    page.wait_for_selector('#busca\\:matriz')
                    page.locator('#busca\\:matriz').nth(0).select_option(matriz_value)

                    search_button = page.locator('#busca > table > tfoot > tr > td > input[type=submit]:nth-child(1)').nth(0)
                    search_button.click()

                    page.wait_for_selector('#resultado\\:detalhar')
                    detalhar = page.locator('#resultado\\:detalhar')

                    if detalhar.count() == 0:
                        page.go_back()
                        page.wait_for_selector('#busca\\:curso')
                        continue

                    detalhar.nth(0).click()

                    page.wait_for_selector('#formulario > table')

                    detail_program = extract_detail_program(page)
                    print(detail_program.courses)

                    page.go_back()
                    page.go_back()
                    page.wait_for_selector('#busca\\:curso')



    def logoff(self) -> None:
        req = self._browser.request
        resp = req.get("/sigaa/logar.do?dispatch=logOff")
        if not (200 <= resp.status < 400):
            raise ValueError("SIGAA: Invalid status code in logoff page.")
