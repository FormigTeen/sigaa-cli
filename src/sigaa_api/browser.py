from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Iterator, List, Optional
from urllib.parse import urljoin

from playwright.sync_api import (
    APIRequestContext,
    APIResponse,
    Browser,
    BrowserContext,
    Locator as PWLocator,
    Page,
    Playwright,
    TimeoutError as PWTimeoutError,
    sync_playwright,
)


@dataclass
class BrowserConfig:
    base_url: str
    headless: bool = True


class ResponseAdapter:
    def __init__(self, resp: APIResponse) -> None:
        self._resp = resp

    @property
    def status(self) -> int:
        return self._resp.status

    def raise_for_status(self) -> None:
        status = self.status
        if not (200 <= status < 400):
            raise RuntimeError(f"HTTP error: status={status}")

    def body(self) -> bytes:
        return self._resp.body()


class RequestClient:
    def __init__(self, request: APIRequestContext, base_url: str) -> None:
        self._request = request
        self._base_url = base_url.rstrip("/") + "/"

    def get(self, url: str, **kwargs: Any) -> ResponseAdapter:
        full = url if url.startswith("http") else urljoin(self._base_url, url)
        resp = self._request.get(full, **kwargs)
        return ResponseAdapter(resp)

    def post(
        self,
        url: str,
        *,
        form: Optional[dict[Any, Any]] = None,
        data: Optional[dict[Any, Any]] = None,
        **kwargs: Any,
    ) -> ResponseAdapter:
        # Mantém compatibilidade: se "data" for dict, envia como form-urlencoded
        full = url if url.startswith("http") else urljoin(self._base_url, url)
        if data is not None and isinstance(data, dict):
            resp = self._request.post(full, form=data, **kwargs)
        elif form is not None:
            resp = self._request.post(full, form=form, **kwargs)
        else:
            resp = self._request.post(full, data=data, **kwargs)
        return ResponseAdapter(resp)


class NodeAdapter:
    def __init__(self, locator: PWLocator, page: "HtmlPage") -> None:
        self._loc = locator
        self._page = page

    def click(self) -> None:
        try:
            self._loc.click()
        except PWTimeoutError:
            return None

    def inner_html(self) -> str:
        try:
            return self._loc.inner_html() or ""
        except PWTimeoutError:
            return ""

    def text_content(self) -> str:
        try:
            tc = self._loc.text_content()
            return tc if tc is not None else ""
        except PWTimeoutError:
            return ""

    def get_attribute(self, name: str) -> Optional[str]:
        try:
            return self._loc.get_attribute(name)
        except PWTimeoutError:
            return None

    def locator(self, selector: str) -> "Locator":
        return Locator(self._loc.locator(selector), self._page)

    def __str__(self) -> str:
        return self.inner_html()


class Locator:
    def __init__(self, locator: PWLocator, page: "HtmlPage") -> None:
        self._loc = locator
        self._page = page

    def count(self) -> int:
        try:
            return self._loc.count()
        except PWTimeoutError:
            return 0

    def nth(self, index: int) -> NodeAdapter:
        return NodeAdapter(self._loc.nth(index), self._page)

    def all(self) -> List[NodeAdapter]:
        try:
            items = self._loc.all()
        except Exception:
            items = []
        return [NodeAdapter(it, self._page) for it in items]

    def __str__(self) -> str:
        if self.count() > 0:
            return self.nth(0).inner_html()
        return ""


class HtmlPage:
    def __init__(self, page: Page, base_url: str) -> None:
        self._page = page
        self._base_url = base_url.rstrip("/") + "/"

    @property
    def url(self) -> str:
        return self._page.url

    def abs_url(self, href: str) -> str:
        return urljoin(self.url, href)

    def goto(self, url: str) -> None:
        full = urljoin(self._base_url, url)
        self._page.goto(full)

    def safe_goto(self, url: str) -> None:
        if url not in self.url:
            self.goto(url)

    def go_back(self) -> None:
        try:
            self._page.go_back()
        except PWTimeoutError:
            return None

    def wait_for_selector(self, selector: str, timeout: int = 10000) -> None:
        try:
            self._page.wait_for_selector(selector, timeout=timeout)
        except PWTimeoutError:
            return None

    def wait_for_load_state(self, state: str = "networkidle") -> None:
        try:
            self._page.wait_for_load_state(state)
        except PWTimeoutError:
            return None

    def content(self) -> str:
        return self._page.content()

    def locator(self, selector: str) -> Locator:
        return Locator(self._page.locator(selector), self)


class SigaaBrowser:
    def __init__(self, config: BrowserConfig) -> None:
        self._config = config
        self._pw: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None

    def ensure_started(self) -> None:
        if self._context is not None:
            return
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=self._config.headless)
        self._context = self._browser.new_context(base_url=self._config.base_url, accept_downloads=True)

    def new_page(self) -> HtmlPage:
        self.ensure_started()
        assert self._context is not None
        page = self._context.new_page()
        return HtmlPage(page, self._config.base_url)

    @property
    def request(self) -> RequestClient:
        self.ensure_started()
        assert self._context is not None
        return RequestClient(self._context.request, self._config.base_url)

    def close(self) -> None:
        if self._context is not None:
            try:
                self._context.close()
            except Exception:
                pass
            self._context = None
        if self._browser is not None:
            try:
                self._browser.close()
            except Exception:
                pass
            self._browser = None
        if self._pw is not None:
            try:
                self._pw.stop()
            except Exception:
                pass
            self._pw = None

    @contextmanager
    def page(self) -> Iterator[HtmlPage]:
        p = self.new_page()
        try:
            yield p
        finally:
            try:
                # Fecha a página subjacente
                # Atributo protegido para encerrar o recurso corretamente
                p._page.close()  # type: ignore[attr-defined]
            except Exception:
                pass
