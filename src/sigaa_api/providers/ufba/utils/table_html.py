from typing import Any, List, NamedTuple

from src.sigaa_api.browser import HtmlPage, Locator, NodeAdapter


def get_rows(table: Locator) -> List[NodeAdapter]:
    return table.nth(0).locator('tbody > tr').all()

# Tuple = (image, name, curso/departamento, formação/matricula, email)
Card = NamedTuple(
    'Card', [("img_src", str), ("name", str), ("location", str), ("code", str), ("email", str)]
)
def extract_cards(table: Locator) -> list[Card]:
    cards: list[Card] = []
    rows = get_rows(table)
    for row in rows:
        tds = row.locator('td').all()
        i = 0
        while i < len(tds):
            img_td = tds[i]
            # Candidate photo cell must contain an <img>
            if img_td.locator('img').count() > 0 and (i + 1) < len(tds):
                info_td = tds[i + 1]
                # Info cell should contain a <strong> with the name
                strong = info_td.locator('strong')
                if strong.count() > 0:
                    name = (strong.nth(0).text_content() or '').strip()

                    # Extract the three labeled lines from the info cell text
                    raw_lines = (info_td.text_content() or '').splitlines()
                    lines = [ln.strip() for ln in raw_lines if ln and ln.strip()]

                    curso_dep = ''
                    form_matr = ''
                    email_line = ''
                    for ln in lines:
                        ln_norm = ln.lower()
                        if not curso_dep and (ln_norm.startswith('curso:') or ln_norm.startswith('departamento:')):
                            curso_dep = ln
                            continue
                        if not form_matr and (
                            ln_norm.startswith('formação:')
                            or ln_norm.startswith('formacao:')
                            or ln_norm.startswith('matrícula:')
                            or ln_norm.startswith('matricula:')
                        ):
                            form_matr = ln
                            continue
                        if not email_line and (
                            ln_norm.startswith('e-mail:')
                            or ln_norm.startswith('email:')
                            or ln_norm.startswith('e-mail :')
                        ):
                            email_line = ln

                    # Photo URL (absolute)
                    img_src = img_td.locator('img').nth(0).get_attribute('src') or ''
                    cards.append(
                        Card(img_src, name, curso_dep, form_matr, email_line)
                    )

                    # Skip over the info cell and optional action cell
                    if (i + 2) < len(tds) and tds[i + 2].locator('a.naoImprimir').count() > 0:
                        i += 3
                    else:
                        i += 2
                    continue
            i += 1

    return cards
