from collections import namedtuple
from typing import List, Optional, NamedTuple

from src.sigaa_cli.browser import HtmlPage, Locator, NodeAdapter
from src.sigaa_cli.providers.ufba.utils.table_html import extract_cards, Card
from src.sigaa_cli.utils.parser import strip_html_bs4


def get_table(page: HtmlPage) -> Locator:
    return page.locator('#turmas-portal > table:nth-child(3)')

def is_valid_active_course_line(line_table: NodeAdapter) -> bool:
    cols = line_table.locator('td')
    return cols.count() >= 3 and cols.nth(0).get_attribute('colspan') is None

def get_active_course(line: NodeAdapter) -> tuple[str, str, str]:
    cols = line.locator('td')

    name = strip_html_bs4(cols.nth(0).inner_html() or '').strip()
    location = strip_html_bs4(cols.nth(1).inner_html() or '').strip()
    time_code = strip_html_bs4(cols.nth(2).inner_html() or '').strip()

    return name, location, time_code


DetailPage = NamedTuple(
    'DetailPage',
    [
        ('name', str),
        ('count', str),
        ('teachers', list[Card]),
        ('students', list[Card]),
    ]
)
def to_detail_page_and_extract(page: HtmlPage, active_course_line: NodeAdapter) -> Optional[DetailPage]:
    link_node = active_course_line.locator('td.descricao a').nth(0)
    if link_node:
        try:
            link_node.click()
            page.wait_for_selector('#formMenu\\:j_id_jsp_1857845999_73 > div.rich-panelbar-content-exterior > table > tbody > tr > td > a:nth-child(4)')

            menu_link_node = page.locator('#formMenu\\:j_id_jsp_1857845999_73 > div.rich-panelbar-content-exterior > table > tbody > tr > td > a:nth-child(4)').nth(0)
            menu_link_node.click()
            page.wait_for_selector('#nomeTurma')

            name_html = page.locator('#nomeTurma').nth(0).inner_html()
            name = strip_html_bs4(name_html).strip()
            
            count_html = page.locator('#j_id_jsp_345573504_153_body > div:nth-child(1) > i').nth(0).inner_html()
            count = strip_html_bs4(count_html)
            
            teacher_table = page.locator('#j_id_jsp_345573504_298 > table:nth-child(3)')
            teachers = extract_cards(teacher_table)
            student_table = page.locator('#j_id_jsp_345573504_298 > table:nth-child(6)')
            students = extract_cards(student_table)

            page.go_back()
            page.go_back()
            page.wait_for_selector('#turmas-portal')

            detail = DetailPage(name, count, teachers, students)
            return detail
        except Exception:
            return None
    return None
