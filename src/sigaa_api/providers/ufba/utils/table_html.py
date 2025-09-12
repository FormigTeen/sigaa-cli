from typing import Any

from src.sigaa_api.browser import HtmlPage, Locator


def get_rows(table: Locator) -> Locator:
    return table.nth(0).locator('tbody > tr')
