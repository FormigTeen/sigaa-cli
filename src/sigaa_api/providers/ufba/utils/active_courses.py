from src.sigaa_api.browser import HtmlPage, Locator


def get_table(page: HtmlPage) -> Locator:
    return page.locator('#turmas-portal > table:nth-child(3)')
