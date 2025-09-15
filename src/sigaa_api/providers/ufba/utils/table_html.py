from typing import Any, List, NamedTuple

from src.sigaa_api.browser import HtmlPage, Locator, NodeAdapter
from src.sigaa_api.utils.list import chunk_after


def get_rows(table: Locator) -> List[NodeAdapter]:
    return table.nth(0).locator('tbody > tr').all()

# Tuple = (image, name, curso/departamento, formação/matricula, email)
Card = NamedTuple(
    'Card', [("img_src", str), ("name", str), ("location", str), ("code", str), ("email", str)]
)
def extract_cards(table: Locator) -> list[Card]:

    def get_img_src(candidate: NodeAdapter) -> str:
        img_html = candidate.locator('img').nth(0)
        return img_html.get_attribute('src') or ''

    def get_name(candidate: NodeAdapter) -> str:
        return (candidate.locator('strong').nth(0).text_content() or '').strip()

    def get_other_lines(candidate: NodeAdapter) -> List[str]:
        raw_lines = (candidate.text_content() or '').splitlines()
        return [raw_line.strip() for raw_line in raw_lines if raw_line and raw_line.strip()]

    def is_course_label(candidate: str) -> bool:
        return candidate.lower().startswith('curso:') or candidate.lower().startswith('departamento:')

    def is_code_label(candidate: str) -> bool:
        return (candidate.lower().startswith('formação:') or
                candidate.lower().startswith('formacao:') or
                candidate.lower().startswith('matrícula:') or
                candidate.lower().startswith('matricula:'))

    def is_email_label(candidate: str) -> bool:
        return candidate.lower().startswith('email:') or candidate.lower().startswith('e-mail:') or candidate.lower().startswith('e-mail:')

    def has_cards_in_row(candidate: NodeAdapter) -> bool:
        return candidate.locator('td').count() >= 2 and candidate.locator('td > img').count() >= 1

    def is_button_card(candidate: NodeAdapter) -> bool:
        return candidate.locator('a.naoImprimir').count() > 0

    cards: list[Card] = []
    rows = [row for row in get_rows(table) if has_cards_in_row(row)]
    tds_in_rows = [row.locator('td').all() for row in rows]
    tds_cards_in_rows = [chunk_after(tds_in_row, is_button_card) for tds_in_row in tds_in_rows]
    td_cards = [list(td_card) for td_cards_in_row in tds_cards_in_rows for td_card in td_cards_in_row]
    td_cards = [td_card for td_card in td_cards if len(td_card) >= 2]

    for tds in td_cards:
        [img_td, info_td, *_] = tds
        img_src = get_img_src(img_td)
        name = get_name(info_td)
        lines = get_other_lines(info_td)

        curso_dep = next(filter(is_course_label, lines), None) or ''
        form_matr = next(filter(is_code_label, lines), None) or ''
        email_line = next(filter(is_email_label, lines), None) or ''

        cards.append(Card(img_src, name, curso_dep, form_matr, email_line))

    return cards
