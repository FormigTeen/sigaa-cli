from __future__ import annotations
from tinydb import TinyDB, Query
from typing import Optional, List
from .browser import BrowserConfig, SigaaBrowser
from src.sigaa_api.providers.ufba.provider import UFBAProvider
from .models.account import Account
from .models.course import RequestedCourse
from .models.program import DetailedProgram
from .models.section import ActiveSection
from .parser import Parser
from .providers.provider import Provider
from src.sigaa_api.utils.database import dump, load, get_database
from .session import Session
from .types import LoginStatus
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
        self._session = Session(institution=final_institution)
        self._parser = parser or Parser()

        # Apenas UFBA
        self._provider: Provider = self._provider_class(self._browser, self._session)
        self._account: Optional[Account] = None
        self._active_courses: Optional[List[ActiveSection]] = None

    def login(self, username: Optional[str] = None, password: Optional[str] = None) -> bool:
        if self._session.login_status == LoginStatus.UNAUTHENTICATED:
            self._provider.login(get_config_if_none(USER_KEY, username) or '', get_config_if_none(PASSWORD_KEY, password) or '')
        self._session.login_status = LoginStatus.AUTHENTICATED
        return True

    def get_database(self) -> TinyDB:
        return get_database(self._provider.KEY)

    def logoff(self) -> bool:
        if self._session.login_status == LoginStatus.AUTHENTICATED:
            self._account = None
        self._session.login_status = LoginStatus.UNAUTHENTICATED
        return True

    def get_account(self) -> Account:
        with self.get_database() as db:
            if self._session.login_status == LoginStatus.UNAUTHENTICATED:
                raise ValueError("Not authenticated")
            account = Account(
                provider=self._provider.KEY,
                registration=self._provider.get_registration() or '',
                name=self._provider.get_name(),
                email=self._provider.get_email(),
                profile_picture_url=self._provider.get_profile_picture_url() or '',
                program=self._provider.get_program(),
            )
            db.table('accounts').upsert(
                dump(account), Query().registration == account.registration
            )
            return account

    def close(self) -> None:
        self._browser.close()

    def get_active_sections(self) -> List[ActiveSection]:
        if self._session.login_status == LoginStatus.UNAUTHENTICATED:
            raise ValueError("Not authenticated")
        if self._active_courses is not None:
            return self._active_courses
        courses = self._provider.get_active_courses()
        self._active_courses = courses
        return courses

    def get_programs(self, no_cache: bool = False) -> List[DetailedProgram]:
        with self.get_database() as db:
            if self._session.login_status == LoginStatus.UNAUTHENTICATED:
                raise ValueError("Not authenticated")
            if not no_cache:
                print("Verificando se há Cursos salvos...")
                raw_saved_programs = db.table('programs').all()
                if len(raw_saved_programs) > 0:
                    return [load(DetailedProgram, program) for program in raw_saved_programs]
            print("Buscando Cursos...")
            programs = self._provider.get_programs()
            print("Salvando " + str(len(programs)) + " Cursos...")
            for program in programs:
                db.table('programs').upsert(dump(program), Query().id_ref == program.id_ref)
            print("Cursos salvos!")
            return programs

    def get_sections(self) -> bool:
        with self.get_database() as db:
            if self._session.login_status == LoginStatus.UNAUTHENTICATED:
                raise ValueError("Not authenticated")
            raw_saved_sections = db.table('sections').all()
            print("Verificando se há Turmas salvas...")
            if raw_saved_sections and len(raw_saved_sections) > 0:
                return True
            print("Buscando Turmas...")
            sections = self._provider.get_sections()
            print("Salvando " + str(len(sections)) + " Turmas...")
            for section in sections:
                db.table('sections').upsert(dump(section), Query().id_ref == section.id_ref)
            print("Turmas salvas!")
            return True

    def get_courses(self, no_cache: bool = False) -> list[RequestedCourse]:
        with self.get_database() as db:
            if self._session.login_status == LoginStatus.UNAUTHENTICATED:
                raise ValueError("Not authenticated")
            if not no_cache:
                raw_saved_courses = db.table('courses').all()
                print("Verificando se há Disciplinas salvas...")
                if len(raw_saved_courses) > 0:
                    return [load(RequestedCourse, course) for course in raw_saved_courses]
            print("Buscando Cursos...")
            programs = self.get_programs()
            print("Cursos capturados...")
            if len(programs) <= 0:
                raise ValueError("No programs")
            simple_courses = (course for program in programs for course in program.courses)
            ids = set(course.id_ref for course in simple_courses)
            print("Encontrando " + str(len(ids)) + " para buscar")
            courses = list(self._provider.get_course(id_ref) for id_ref in ids)
            print("Salvando " + str(len(courses)) + " Cursos...")
            for course in courses:
                db.table('courses').upsert(
                    dump(course), Query().id_ref == course.id_ref
                )
            print("Cursos salvos!")
            return courses
