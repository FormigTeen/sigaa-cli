from typing import NamedTuple, List
import re

from src.sigaa_api.browser import HtmlPage
from src.sigaa_api.utils.parser import strip_html_bs4

# Course entry as shown in the curriculum tables
Course = NamedTuple('Course', [
    ('code', str),
    ('title', str),
    ('mode', str),
    ('type', str),
    ('level', str),
    ('id_ref', str),
])

DetailProgram = NamedTuple('DetailProgram', [
    ('code', str),
    ('curriculum_title', str),
    ('courses', List[Course])
])


def _text_by_selector(page: HtmlPage, selector: str) -> str:
    loc = page.locator(selector)
    if loc.count() == 0:
        return ""
    html = loc.nth(0).inner_html() or ""
    text = strip_html_bs4(html)
    # Normalize whitespace/newlines
    lines = [ln.strip() for ln in text.splitlines() if ln and ln.strip()]
    return " ".join(lines).strip()


def extract_detail_program(page: HtmlPage) -> DetailProgram:
    # Top info table
    code = _text_by_selector(page, '#formulario > table > tbody > tr:nth-child(1) > td')
    curriculum_title = _text_by_selector(page, '#formulario > table > tbody > tr:nth-child(2) > td')

    # Courses from tab panel
    courses: List[Course] = []
    tab_panel = page.locator('#formulario\\:tab_painel')
    if tab_panel.count() > 0:
        # Each tab content is a TD with an id inside the second TR
        tab_contents = tab_panel.nth(0).locator('> tbody > tr:nth-child(2) > td[id]').all()
        for content in tab_contents:
            # Get section/level title (first span within content)
            level_span = content.locator('span')
            level_name = ''
            if level_span.count() > 0:
                level_name = strip_html_bs4(level_span.nth(0).inner_html() or '').strip()

            # Now iterate the data tables within this content
            tables = content.locator('table.rich-table').all()
            for tbl in tables:
                rows = tbl.locator('tbody > tr')
                total = rows.count()
                for i in range(total):
                    row = rows.nth(i)
                    tds = row.locator('td')
                    td_count = tds.count()
                    if td_count < 3:
                        continue

                    # Column mapping: (code, title, mode, [type])
                    code_td = tds.nth(0)
                    # Prefer the label inside the first td when available
                    label = code_td.locator('label')
                    if label.count() > 0:
                        code_text = strip_html_bs4(label.nth(0).inner_html() or '')
                        # Extract id_ref from onclick attribute
                        onclick = label.nth(0).get_attribute('onclick') or ''
                        m = re.search(r"PainelComponente\.show\((\d+),", onclick)
                        id_ref = m.group(1) if m else ''
                    else:
                        code_text = strip_html_bs4(code_td.inner_html() or '')
                        id_ref = ''
                    code_text = code_text.strip()

                    title_text = strip_html_bs4(tds.nth(1).inner_html() or '').strip()
                    mode_text = strip_html_bs4(tds.nth(2).inner_html() or '').strip()

                    if td_count >= 4:
                        type_text = strip_html_bs4(tds.nth(3).inner_html() or '').strip()
                    else:
                        # Tabs without explicit type are mandatory components
                        type_text = 'OBRIGATÓRIO'

                    if code_text and title_text:
                        courses.append(Course(code_text, title_text, mode_text, type_text, level_name, id_ref))

    return DetailProgram(code, curriculum_title, courses)
