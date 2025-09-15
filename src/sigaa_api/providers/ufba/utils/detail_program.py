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
        tab_contents = tab_panel.nth(0).locator('> tbody > tr:nth-child(2) > td[id]').all()
        for content in tab_contents:

            # Get section/level title (first span within content)
            level_span = content.locator('span')
            level_name = ''
            if level_span.count() > 0:
                level_name = strip_html_bs4(level_span.nth(0).inner_html() or '').strip()

            # Now iterate the data tables within this content
            tables = content.locator('table.rich-table').all()
            rows_in_tables = [tbl.locator('tbody > tr').all() for tbl in tables]

            for rows in rows_in_tables:
                tds_in_row = [row.locator('td') for row in rows]
                tds_in_row = [tds for tds in tds_in_row if tds.count() >= 3]

                types = [None if tds.count() < 4 else tds.nth(3).inner_html() or '' for tds in tds_in_row]
                str_types = ['OBRIGATÓRIO' if type_html is None else strip_html_bs4(type_html) for type_html in types]
                types = [type_label.strip() for type_label in str_types]

                code_tds = [tds.nth(0) for tds in tds_in_row]
                labels_html = [code_td.locator('label') for code_td in code_tds]
                labels_locator_html = [None if label.count() < 0 else label.nth(0) for label in labels_html]

                codes = ['' if label_html is None else strip_html_bs4(label_html.inner_html() or '') for label_html in labels_locator_html]

                onclick_labels = ['' if label_html is None else label_html.get_attribute('onclick') or '' for label_html in labels_locator_html]
                onclick_regex_labels = [re.search(r"PainelComponente\.show\((\d+),", onclick_text) for onclick_text in onclick_labels]
                ids = [regex_onclick.group(1) if regex_onclick else '' for regex_onclick in onclick_regex_labels]

                titles_html = [(tds.nth(1).inner_html() or '') for tds in tds_in_row]
                titles = [strip_html_bs4(title_html).strip() for title_html in titles_html]

                modes_html = [tds.nth(2).inner_html() or '' for tds in tds_in_row]
                modes = [strip_html_bs4(mode_html).strip() for mode_html in modes_html]

                table_courses = list(zip(codes, titles, modes, types, [level_name] * len(ids), ids))
                table_tuple_courses = [Course(*props) for props in table_courses]

                courses += table_tuple_courses

    return DetailProgram(code, curriculum_title, courses)
