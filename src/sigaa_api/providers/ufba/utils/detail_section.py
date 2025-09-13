from typing import NamedTuple, List, Optional
import re

from src.sigaa_api.browser import HtmlPage, NodeAdapter
from src.sigaa_api.utils.parser import strip_html_bs4

Spot = NamedTuple('Spot', [
    ('course', str),
    ('count', str)
])

Section = NamedTuple('Section', [
    ('ref_id', str),
    ('course', str),
    ('term', str),
    ('teachers', list[str]),
    ('mode', str),
    ('time_id', str),
    ('location', str),
    ('spots', list[Spot]),
])
def _normalize_text(text: str) -> str:
    lines = [ln.strip() for ln in (text or '').splitlines() if ln and ln.strip()]
    return re.sub(r"\s+", " ", " ".join(lines)).strip()


def _extract_course_from_header(row: NodeAdapter) -> str:
    # Get the closest preceding header row with class 'destaque'
    header_td = row.locator('xpath=preceding-sibling::tr[contains(@class,"destaque")][1]/td')
    if header_td.count() == 0:
        return ''
    html = header_td.nth(0).inner_html() or ''
    return _normalize_text(strip_html_bs4(html))


def _extract_ref_id(row: NodeAdapter) -> str:
    a = row.locator('td:nth-child(2) a')
    if a.count() == 0:
        return ''
    onclick = a.nth(0).get_attribute('onclick') or ''
    m = re.search(r"PainelTurma\.show\((\d+)\)", onclick)
    return m.group(1) if m else ''


def _extract_basic_from_row(row: NodeAdapter) -> tuple[str, str, str, str]:
    tds = row.locator('td')
    term = _normalize_text(strip_html_bs4(tds.nth(0).inner_html() or '')) if tds.count() > 0 else ''
    mode = _normalize_text(strip_html_bs4(tds.nth(4).inner_html() or '')) if tds.count() > 4 else ''
    # Horário (remove intervalo de datas entre parênteses)
    horario_full = _normalize_text(strip_html_bs4(tds.nth(6).inner_html() or '')) if tds.count() > 6 else ''
    time_id = re.sub(r"\s*\(.*\)\s*$", "", horario_full).strip()
    location = _normalize_text(strip_html_bs4(tds.nth(7).inner_html() or '')) if tds.count() > 7 else ''
    return term, mode, time_id, location


def _extract_teachers_and_spots(page: HtmlPage) -> tuple[List[str], List[Spot]]:
    teachers: List[str] = []
    spots: List[Spot] = []

    # Target table under #resumo
    tbl = page.locator('#resumo > table > tbody > tr > td > table')
    if tbl.count() == 0:
        return teachers, spots

    # Find all nested tables (subformluario)
    nested_tables = tbl.nth(0).locator('table').all()
    for nt in nested_tables:
        header = nt.locator('tr.secao > td')
        header_text = _normalize_text(strip_html_bs4(header.nth(0).inner_html() or '')) if header.count() > 0 else ''

        if header_text.startswith('Professores'):
            rows = nt.locator('tr').all()
            for i, r in enumerate(rows):
                # skip header row
                if i == 0 and 'secao' in (r.get_attribute('class') or ''):
                    continue
                t = _normalize_text(strip_html_bs4(r.locator('td').nth(0).inner_html() or ''))
                if t:
                    teachers.append(t)

        elif header_text.startswith('Vagas Reservadas'):
            rows = nt.locator('tr').all()
            for i, r in enumerate(rows):
                if i == 0 and 'secao' in (r.get_attribute('class') or ''):
                    continue
                tds = r.locator('td')
                if tds.count() >= 2:
                    course = _normalize_text(strip_html_bs4(tds.nth(0).inner_html() or ''))
                    count = _normalize_text(strip_html_bs4(tds.nth(1).inner_html() or ''))
                    if course and count:
                        spots.append(Spot(course, count))

    return teachers, spots


def go_and_extract_detail_section(row: NodeAdapter, page: HtmlPage) -> Section:
    # Basic info from list row
    ref_id = _extract_ref_id(row)
    course = _extract_course_from_header(row)
    term, mode, time_id, location = _extract_basic_from_row(row)

    # Navigate to detail page
    if ref_id:
        url = f"/sigaa/graduacao/turma/view_painel.jsf?ajaxRequest=true&contarMatriculados=true&id={ref_id}"
        page.goto(url)
        page.wait_for_selector('#resumo')

    teachers, spots = _extract_teachers_and_spots(page)

    # Go back to the list page to continue scraping
    page.go_back()
    page.wait_for_selector('#lista-turmas')

    return Section(ref_id, course, term, teachers, mode, time_id, location, spots)
