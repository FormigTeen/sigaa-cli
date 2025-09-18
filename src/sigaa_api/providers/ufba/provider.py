from __future__ import annotations
import re
from collections.abc import Callable
from typing import Final, Optional, List

from src.sigaa_api.models.entities import ActiveTeacher, ActiveStudent
from src.sigaa_api.models.program import DetailedProgram, Program
from src.sigaa_api.models.section import Section, DetailedSection, ActiveSection, Spot
from src.sigaa_api.providers.provider import Provider
from src.sigaa_api.providers.ufba.utils.active_courses import get_table as get_active_courses_table, \
    is_valid_active_course_line, get_active_course, to_detail_page_and_extract
from src.sigaa_api.providers.ufba.utils.detail_program import extract_detail_program, Course, DetailProgram
from src.sigaa_api.providers.ufba.utils.detail_section import go_and_extract_detail_section, Spot as UnsafeSpot
from src.sigaa_api.providers.ufba.utils.elements import extract_times
from src.sigaa_api.providers.ufba.utils.table_html import get_rows, Card
from src.sigaa_api.utils.compiler import fnd_array
from src.sigaa_api.utils.host import add_uri
from src.sigaa_api.utils.parser import strip_html_bs4
from src.sigaa_api.models.course import AnchoredCourse, Course as ModelCourse, RequestedCourse
from src.sigaa_api.utils.text import strip_parentheses_terms, extract_sequence


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

    def get_active_courses(self) -> List[ActiveSection]:
        def parse_teacher(teacher: Card) -> ActiveTeacher:
            img_url = add_uri(self.get_host(), teacher.img_src)
            email = teacher.email.lower().replace('e-mail:', '').strip()
            department = teacher.location.upper().replace('DEPARTAMENTO:', '').strip()
            education = teacher.code.upper().replace("FORMAÇÃO:", "").strip()
            return ActiveTeacher(name=teacher.name.strip(), email=email, department=department, education=education, image_url=img_url)

        def parse_student(student: Card) -> ActiveStudent:
            img_url = add_uri(self.get_host(), student.img_src)
            email = student.email.lower().replace('e-mail:', '').strip()
            [course_label, *_] = student.location.upper().replace('CURSO:', '').strip().split('/', 1)
            registration = student.code.upper().replace("MATRÍCULA:", "").strip()
            return ActiveStudent(name=student.name.strip(), email=email, course_label=course_label, registration=registration, image_url=img_url)

        courses: List[ActiveSection] = []
        with self._browser.page() as p:
            p.goto('/sigaa/portais/discente/discente.jsf')
            tbl = get_active_courses_table(p)
            if tbl.count() == 0:
                return courses

            current_term = self.get_current_term() or ""
            rows = get_rows(tbl)
            rows = list(filter(is_valid_active_course_line, rows))

            for row in rows:
                _, table_location, time_code = get_active_course(row)
                result = to_detail_page_and_extract(p, row)
                title, count, teachers, students, *_ = result if result else ("", "", [], [])
                code, name, *_ = map(str.strip, title.split('-', 1))
                name, class_code = map(str.strip, name.split('- T', 1))
                class_code = "T" + class_code

                [number_classes, total_classes, *_] = list(map(str.strip, count.split('/')))
                course_elment = ModelCourse(
                    name=name,
                    code=code,
                )

                courses.append(
                    ActiveSection(
                        course=course_elment,
                        location_table=table_location,
                        time_codes=extract_times(time_code),
                        term=current_term,
                        class_code=class_code,
                        teachers=list(map(parse_teacher, teachers)),
                        students=list(map(parse_student, students)),
                        total_classes=int(total_classes),
                        number_classes=int(number_classes),
                    )
                )
        return courses

    def get_sections(self) -> List[DetailedSection]:
        sections: list[DetailedSection] = []
        def parse_stop(value: UnsafeSpot) -> Spot:
            [name, location, program_type, mode, time_code, *_] = list(map(str.strip, value.course.split('-')))
            [used, total, *_] = list(map(extract_sequence, value.count.split('/')))
            program = Program(
                title=name,
                location=location,
                program_type=program_type,
                mode=mode,
                time_code=time_code,
            )
            return Spot(
                program=program,
                seats_count=total,
                seats_accepted=used
            )

        with self._browser.page() as page:
            page.goto('/sigaa/ensino/turma/busca_turma.jsf')
            page.wait_for_selector('#busca\\:curso')

            # Itera sobre os cursos, ignorando a primeira opção (placeholder)
            course_options_nodes = page.locator('#form\\:selectCurso > option')
            total_courses = course_options_nodes.count()
            course_options = [course_options_nodes.nth(index) for index in range(1, total_courses)]
            course_option_values = [option.get_attribute('value') for option in course_options]
            course_option_values = [value for value in course_option_values if value]

            for course_value in course_option_values:
                # Seleciona o curso para carregar as matrizes e coletar todos os valores
                page.locator('#form\\:selectCurso ').nth(0).select_option(course_value)
                page.wait_for_selector('#form\\:selectCurso ')

                # Nome legível do curso selecionado (para logging)
                selected_opt = page.locator('#form\\:selectCurso > option:checked')
                course_name = strip_html_bs4(selected_opt.nth(0).inner_html() or '') if selected_opt.count() > 0 else str(course_value)
                [course_name, *_] = list(map(str.strip, course_name.split('-', 1)))

                # Garante que o checkbox de curso esteja sempre marcado
                checkbox_selector = '#form\\:checkCurso'
                checked_selector = '#form\\:checkCurso:checked'
                checkbox = page.locator(checkbox_selector)
                if checkbox.count() > 0:
                    is_checked = page.locator(checked_selector).count() > 0
                    if not is_checked:
                        checkbox.nth(0).click()
                        page.wait_for_selector(checked_selector)

                search_button = page.locator('#form\\:buttonBuscar').nth(0)
                search_button.click()

                page.wait_for_selector('#lista-turmas')
                table = page.locator('#lista-turmas')

                # Itera linhas da tabela, pulando cabeçalhos e linhas de opções
                rows = get_rows(table)
                rows_with_class = [(row, (row.get_attribute('class') or '').lower()) for row in rows]
                rows_with_class = [(row, classes) for row, classes in rows_with_class if 'no-hover' not in classes]
                rows = [row for row, classes in rows_with_class if 'linhapar' in classes or 'linhaimpar' in classes]

                print("Buscando no Curso " + str(course_name) + " as turmas: " + str(len(rows)))

                for row in rows:
                    try:
                        unsafe_section = go_and_extract_detail_section(row, page)
                        [code, *_] = list(map(str.strip, unsafe_section.title.split('-', 1)))
                        course = ModelCourse(code=code, name=course_name)
                        teachers = list(map(strip_parentheses_terms, unsafe_section.teachers))
                        section = DetailedSection(
                            id_ref=unsafe_section.ref_id.strip(),
                            course=course,
                            term=unsafe_section.term.strip(),
                            teachers=teachers,
                            mode=unsafe_section.mode.strip(),
                            time_codes=extract_times(unsafe_section.time_id),
                            location_table=unsafe_section.location.strip(),
                            seats_count=extract_sequence(unsafe_section.total),
                            seats_accepted=extract_sequence(unsafe_section.total_accepted),
                            seats_requested=extract_sequence(unsafe_section.total_requested),
                            seats_rerequested=extract_sequence(unsafe_section.total_rerequested),
                            spots_reserved=list(map(parse_stop, unsafe_section.spots)),
                        )
                        sections.append(section)
                    except Exception as e:
                        print(e)
                        continue

                print("Bsuca das turmas de " + str(course_name) + " finalizado!")
                page.go_back()
                page.wait_for_selector('#busca\\:curso')
            return sections

    def get_course(self, ref_id: str) -> RequestedCourse:
        with self._browser.page() as page:
            page.goto('/sigaa/graduacao/componente/view_painel.jsf?id=' + str(ref_id))
            page.wait_for_selector('body')

            def clean(text: Optional[str]) -> str:
                return (strip_html_bs4(text or '') or '').replace('\n', ' ').strip()

            # Data to fill
            data: dict = {
                'code': None,
                'name': None,
                'department': None,
                'mode': None,
                'prerequisites': [],
                'corequisites': [],
                'equivalences': [],
                'workload_total': None,
            }

            # Map straightforward th -> field name
            th_map = {
                'Código': 'code',
                'Nome': 'name',
                'Unidade Responsável': 'department',
                'Modalidade de Educação': 'mode',
            }

            rows = page.locator('tr')
            for i in range(rows.count()):
                row = rows.nth(i)
                ths = row.locator('th')
                tds = row.locator('td')
                # Handle simple th->td pairs
                if ths.count() > 0 and tds.count() > 0:
                    th_text = clean(ths.nth(0).inner_html())
                    if th_text.endswith(':'):
                        th_text = th_text[:-1].strip()

                    if th_text in th_map:
                        value = clean(tds.nth(0).inner_html())
                        data[th_map[th_text]] = value
                        continue

                    # Complex lists: prerequisites/corequisites/equivalences
                    if th_text in ('Pré-Requisitos', 'Co-Requisitos', 'Equivalências'):
                        value = clean(tds.nth(0).inner_html())
                        value = str(value.replace('-', '').strip())
                        result = []
                        if len(value) > 0:
                            result = fnd_array(value)

                        key = {
                            'Pré-Requisitos': 'prerequisites',
                            'Co-Requisitos': 'corequisites',
                            'Equivalências': 'equivalences',
                        }[th_text]
                        data[key] = result
                        continue

                # Handle workload rows (no th, left cell contains the label)
                if tds.count() >= 2:
                    left = clean(tds.nth(0).inner_html())
                    if 'Total de Carga Horária do Componente' in left:
                        value = clean(tds.nth(1).inner_html())
                        data['workload_total'] = value


            department, location, *_ = data['department'].split('-')
            department, *_ = department.rsplit("/", 1)
            print("Carregando a Disciplina: " + str(data['code']) + " - " + data['name'])
            return RequestedCourse(
                id_ref=ref_id,
                name=data['name'].strip(),
                code=data['code'].strip(),
                department=department.strip(),
                location=location.strip(),
                mode=data['mode'].strip(),
                prerequisites=data['prerequisites'],
                corequisites=data['corequisites'],
                equivalences=data['equivalences'],
            )

    def get_programs(self) -> list[DetailedProgram]:
        programs : List[DetailedProgram] = []
        def parse_course(program: DetailProgram) -> Callable[[Course], AnchoredCourse]:
            def parse(course: Course) -> AnchoredCourse:
                [name, *_] = course.title.split('-')
                return AnchoredCourse(
                    name=name.strip(),
                    code=course.code.strip(),
                    id_ref=course.id_ref.strip(),
                    mode=course.mode.strip(),
                    program_code=program.code.strip(),
                    level=course.level.strip(),
                    type=course.type.strip(),
                )

            return parse

        with self._browser.page() as page:
            page.goto('/sigaa/geral/estrutura_curricular/busca_geral.jsf')
            page.wait_for_selector('#busca\\:curso')

            # Itera sobre os cursos, ignorando a primeira opção (placeholder)
            course_options_nodes = page.locator('#busca\\:curso > option')
            total_courses = course_options_nodes.count()
            course_options = [course_options_nodes.nth(index) for index in range(1, total_courses)]
            course_option_values = [option.get_attribute('value') for option in course_options]
            course_option_values = [value for value in course_option_values if value]

            for course_value in course_option_values:
                # Seleciona o curso para carregar as matrizes e coletar todos os valores
                page.locator('#busca\\:curso').nth(0).select_option(course_value)
                page.wait_for_selector('#busca\\:matriz')

                matriz_options_nodes = page.locator('#busca\\:matriz > option')
                total_matrizes = matriz_options_nodes.count()

                matriz_options = [matriz_options_nodes.nth(index) for index in range(1, total_matrizes)]
                matriz_values = [option.get_attribute('value') for option in matriz_options]

                for matriz_value in matriz_values:
                    page.locator('#busca\\:curso').nth(0).select_option(course_value)
                    page.wait_for_selector('#busca\\:matriz')
                    page.locator('#busca\\:matriz').nth(0).select_option(matriz_value)

                    # Garante que os checkboxes de curso e matriz estejam sempre marcados
                    checkbox_curso_selector = '#busca\\:checkCurso'
                    checked_curso_selector = '#busca\\:checkCurso:checked'
                    checkbox_matriz_selector = '#busca\\:checkMatriz'
                    checked_matriz_selector = '#busca\\:checkMatriz:checked'

                    checkbox_curso = page.locator(checkbox_curso_selector)
                    if checkbox_curso.count() > 0:
                        is_curso_checked = page.locator(checked_curso_selector).count() > 0
                        if not is_curso_checked:
                            checkbox_curso.nth(0).click()
                            page.wait_for_selector(checked_curso_selector)

                    checkbox_matriz = page.locator(checkbox_matriz_selector)
                    if checkbox_matriz.count() > 0:
                        is_matriz_checked = page.locator(checked_matriz_selector).count() > 0
                        if not is_matriz_checked:
                            checkbox_matriz.nth(0).click()
                            page.wait_for_selector(checked_matriz_selector)

                    search_button = page.locator('#busca > table > tfoot > tr > td > input[type=submit]:nth-child(1)').nth(0)
                    search_button.click()

                    page.wait_for_selector('#resultado\\:detalhar')
                    detalhar = page.locator('#resultado\\:detalhar')

                    if detalhar.count() == 0:
                        page.go_back()
                        page.wait_for_selector('#busca\\:curso')
                        continue

                    first_detail = detalhar.nth(0)
                    onclick_attr = first_detail.get_attribute('onclick') or ''
                    match = re.search(r"'id'\s*:\s*'([^']+)'", onclick_attr)
                    id_ref = match.group(1) if match else ''

                    first_detail.click()

                    page.wait_for_selector('#formulario > table')

                    detail_program = extract_detail_program(page)
                    [title, location, program_type, mode, time_code, *_] = list(map(str.strip, detail_program.curriculum_title.split('-')))
                    code = detail_program.code.strip()
                    detailed_program = DetailedProgram(title=title, location=location, program_type=program_type, mode=mode, time_code=time_code,
                                                       code=code.strip(), id_ref=id_ref.strip(),
                                                       courses=list(map(parse_course(detail_program), detail_program.courses)))
                    print(f"Encontrei o Curso ({id_ref}):" + detailed_program.title)
                    programs.append(detailed_program)

                    page.go_back()
                    page.go_back()
                    page.wait_for_selector('#busca\\:curso')

            return programs
