from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from typing import List, Optional

from ..bonds import BondType, StudentBond, TeacherBond
from ..browser import SigaaBrowser
from ..parser import Parser
from ..session import Session
from ..types import LoginStatus, ProgressCallback
from ..courses.models import Course
from ..activities.models import Activity
from datetime import datetime
from ..courses.navigator import CourseNavigator


@dataclass
class SigaaAccountUFBA:
    browser: SigaaBrowser
    parser: Parser
    session: Session

    def __post_init__(self) -> None:
        self._active_bonds: List[BondType] = []
        self._inactive_bonds: List[BondType] = []
        self._name: Optional[str] = None
        self._emails: Optional[List[str]] = None
        self._parsed: bool = False

    def _ensure_parsed(self) -> None:
        if self._parsed:
            return
        # Tenta identificar página inicial: página do discente ou página de vínculos
        with self.browser.page() as p:
            p.goto("/sigaa/portais/discente/discente.jsf")
            url = p.url
            html = p.content()
            if "O sistema comportou-se de forma inesperada" in html:
                raise ValueError("SIGAA: Invalid homepage, the system behaved unexpectedly.")

            if "/portais/discente/discente.jsf" in url:
                self._parse_student_homepage(p)
            else:
                # Alguns fluxos redirecionam para vínculos
                p.goto("/sigaa/vinculos.jsf")
                self._parse_bond_page(p)
        self._parsed = True

    def _parse_bond_page(self, page) -> None:
        rows = page.locator("table.subFormulario tbody tr")
        for i in range(rows.count()):
            row = rows.nth(i)
            tds = row.locator("td")
            if tds.count() == 0:
                continue
            # Tipo do vínculo
            bond_type = row.locator("#tdTipo").text_content()
            if not bond_type:
                bond_type = tds.nth(0).text_content() or ""
            bond_type = self.parser.remove_tags_html(bond_type)

            # Status (Sim/Não)
            status_text = self.parser.remove_tags_html(tds.nth(3).text_content() or "").strip()
            active = status_text == "Sim"

            bond: Optional[BondType] = None
            if bond_type == "Discente":
                registration = self.parser.remove_tags_html(tds.nth(2).text_content() or "")
                program_raw = self.parser.remove_tags_html(tds.nth(4).text_content() or "")
                program = program_raw.replace("Curso: ", "").strip()
                href = row.locator("a[href]").first.get_attribute("href")
                switch_url: Optional[str]
                if href:
                    switch_url = page.abs_url(href)
                else:
                    switch_url = None
                bond = StudentBond(registration=registration, program=program, switch_url=switch_url)
            elif bond_type == "Docente":
                bond = TeacherBond()

            if bond:
                if active:
                    self._active_bonds.append(bond)
                else:
                    self._inactive_bonds.append(bond)

    def _parse_student_homepage(self, page) -> None:
        registration = self.parser.remove_tags_html(
            page.locator('#agenda-docente > table > tbody > tr:nth-child(1) > td:nth-child(2)').text_content()
        )
        program = self.parser.remove_tags_html(
            page.locator('#info-usuario > p.periodo-atual').text_content()
        )
        if not registration:
            raise ValueError('SIGAA: Student bond without registration code.')
        if not program:
            raise ValueError('SIGAA: Student bond program not found.')
        self._active_bonds.append(StudentBond(registration=registration, program=program, switch_url=None))

    # Public API
    def get_active_bonds(self) -> List[BondType]:
        self._ensure_parsed()
        return list(self._active_bonds)

    def get_inactive_bonds(self) -> List[BondType]:
        self._ensure_parsed()
        return list(self._inactive_bonds)

    def logoff(self) -> None:
        req = self.browser.request
        resp = req.get("/sigaa/logar.do?dispatch=logOff")
        if not (200 <= resp.status < 400):
            raise ValueError("SIGAA: Invalid status code in logoff page.")
        self.session.login_status = LoginStatus.UNAUTHENTICATED

    def get_profile_picture_url(self) -> Optional[str]:
        with self.browser.page() as p:
            p.goto('/sigaa/portais/discente/discente.jsf')
            img = p.locator('#perfil-docente > div.pessoal-docente > div.foto > img')
            if img.count() == 0:
                return None
            src = img.nth(0).get_attribute('src')
            if not src:
                return None
            url = p.abs_url(src)
            return url

    def download_profile_picture(self, basepath: Path, callback: Optional[ProgressCallback] = None) -> Optional[Path]:
        url = self.get_profile_picture_url()
        if not url:
            return None
        basepath.mkdir(parents=True, exist_ok=True)
        resp = self.browser.request.get(url)
        resp.raise_for_status()
        content = resp.body()
        total = len(content)
        if callback:
            callback(total, total)
        filename = url.split('/')[-1] or 'photo.jpg'
        dest = basepath / filename
        dest.write_bytes(content)
        return dest

    def get_name(self) -> str:
        if self._name is not None:
            return self._name
        with self.browser.page() as p:
            p.goto('/sigaa/portais/discente/discente.jsf')
            html = p.locator('#info-usuario > p.usuario > span').nth(0).inner_html()
            self._name = self.parser.remove_tags_html(html)
            return self._name

    def get_emails(self) -> List[str]:
        if self._emails is not None:
            return list(self._emails)
        with self.browser.page() as p:
            p.goto('/sigaa/portais/discente/discente.jsf')
            self._emails = []
            tbl = p.locator('#agenda-docente > table')
            if tbl.count() == 0:
                return []
            rows = tbl.nth(0).locator('tr')
            for i in range(rows.count()):
                row = rows.nth(i)
                tds = row.locator('td')
                if tds.count() < 2:
                    continue
                key = self.parser.remove_tags_html(tds.nth(0).inner_html() or '').strip().lower()
                if key in ('e-mail:', 'e-mail'):
                    value = self.parser.remove_tags_html(tds.nth(1).inner_html() or '')
                    if value:
                        self._emails.append(value)
                    break
        return list(self._emails)

    # Bonds
    def switch_bond_by_registration(self, registration: str) -> None:
        # Procura por vínculo com a matrícula e usa o switch_url
        self._ensure_parsed()
        candidates: List[StudentBond] = [
            b for b in self._active_bonds + self._inactive_bonds if isinstance(b, StudentBond)
        ]
        for b in candidates:
            if b.registration == registration and b.switch_url:
                with self.browser.page() as p:
                    p.goto(b.switch_url)
                return
        raise ValueError("SIGAA: Bond switch url could not be found for this registration.")

    # Courses
    def get_courses(self) -> List[Course]:
        with self.browser.page() as p:
            p.goto('/sigaa/portais/discente/turmas.jsf')
            rows = p.locator('table.listagem > tbody > tr')
            courses: List[Course] = []
            for i in range(rows.count()):
                row = rows.nth(i)
                tds = row.locator('td')
                if tds.count() < 5:
                    continue
                title = self.parser.remove_tags_html(tds.nth(0).inner_html() or '')
                code = self.parser.remove_tags_html(tds.nth(1).inner_html() or '') or None
                schedule = self.parser.remove_tags_html(tds.nth(2).inner_html() or '') or None
                num_text = self.parser.remove_tags_html(tds.nth(3).inner_html() or '')
                try:
                    number = int(''.join(ch for ch in num_text if ch.isdigit())) if num_text else None
                except Exception:
                    number = None
                period = self.parser.remove_tags_html(tds.nth(4).inner_html() or '') or None
                onclick = row.locator('a[onclick]')
                open_js_trigger = onclick.nth(0).get_attribute('onclick') if onclick.count() > 0 else None
                courses.append(Course(title=title, code=code, schedule=schedule, number_of_students=number, period=period, open_js_trigger=open_js_trigger))
            return courses

    def get_activities(self) -> List[Activity]:
        with self.browser.page() as p:
            p.goto('/sigaa/portais/discente/discente.jsf')
            table = p.locator('#avaliacao-portal > table')
            rows = table.locator('tbody > tr')
            acts: List[Activity] = []
            for i in range(rows.count()):
                row = rows.nth(i)
                tds = row.locator('td')
                if tds.count() < 3:
                    continue
                date_cell = self.parser.remove_tags_html(tds.nth(1).inner_html() or '')
                # Simplista: extrai dd/mm/aaaa hh:mm
                # UFBA pode fornecer data curta; tenta parse básico
                date_txt = ' '.join(date_cell.split())
                # heurística mínima
                try:
                    # tenta formato dd/mm/aaaa hh:mm
                    parts = date_txt.split()
                    if parts:
                        dmy = parts[0]
                        hm = parts[1] if len(parts) > 1 else '00:00'
                        day, month, year = dmy.split('/')
                        if len(year) == 2:
                            year = '20' + year
                        hour, minute = hm.split(':')
                        dt = datetime(int(year), int(month), int(day), int(hour), int(minute))
                    else:
                        dt = datetime.now()
                except Exception:
                    dt = datetime.now()

                done = False
                try:
                    imgsrc = tds.nth(0).locator('img').nth(0).get_attribute('src') or ''
                    if 'check.png' in imgsrc:
                        done = True
                except Exception:
                    done = dt.timestamp() < datetime.now().timestamp()

                small = tds.nth(2).locator('small')
                info_lines: List[str] = []
                if small.count():
                    # tenta pegar quebras em <br>
                    html = small.nth(0).inner_html()
                    info_lines = [s for s in self.parser.remove_tags_html(html).split('\n') if s.strip()]
                if len(info_lines) >= 2:
                    course_title = info_lines[0]
                    rest = info_lines[1]
                    if ': ' in rest:
                        typ, title = rest.split(': ', 1)
                    else:
                        typ, title = 'Atividade', rest
                else:
                    course_title, typ, title = 'Curso', 'Atividade', 'Sem título'
                acts.append(Activity(course_title=course_title, type=typ, title=title, date=dt, done=done))
            return acts

    def open_course_by_title(self, title: str) -> CourseNavigator:
        return CourseNavigator(self.browser, self.parser).open_course_by_title(title)
