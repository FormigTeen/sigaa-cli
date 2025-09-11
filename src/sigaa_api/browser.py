from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterable, List, Optional, Any, Iterator
from urllib.parse import urljoin

import httpx
from selectolax.parser import HTMLParser, Node


@dataclass
class BrowserConfig:
    base_url: str
    headless: bool = True  # kept for compatibility; no effect for httpx


class ResponseAdapter:
    def __init__(self, resp: httpx.Response) -> None:
        self._resp = resp

    @property
    def status(self) -> int:
        return self._resp.status_code

    def raise_for_status(self) -> None:
        self._resp.raise_for_status()

    def body(self) -> bytes:
        return self._resp.content


class RequestClient:
    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    def get(self, url: str, **kwargs: Any) -> ResponseAdapter:
        resp = self._client.get(url, **kwargs)
        return ResponseAdapter(resp)

    def post(self, url: str, *, form: Optional[dict[Any, Any]] = None, data: Optional[dict[Any, Any]] = None, **kwargs: Any) -> ResponseAdapter:
        payload = data if data is not None else form
        resp = self._client.post(url, data=payload, **kwargs)
        return ResponseAdapter(resp)


class NodeAdapter:
    def __init__(self, node: Node, page: "HtmlPage") -> None:
        self._node = node
        self._page = page

    def inner_html(self) -> str:
        return self._node.html or ""

    def text_content(self) -> str:
        return self._node.text() or ""

    def get_attribute(self, name: str) -> Optional[str]:
        return self._node.attributes.get(name)

    def locator(self, selector: str) -> "Locator":
        nodes = self._node.css(selector) or []
        return Locator(nodes, self._page)


class Locator:
    def __init__(self, nodes: Iterable[Node], page: "HtmlPage") -> None:
        self._nodes: List[Node] = list(nodes)
        self._page = page

    def count(self) -> int:
        return len(self._nodes)

    def nth(self, index: int) -> NodeAdapter:
        return NodeAdapter(self._nodes[index], self._page)

    def all(self) -> List[NodeAdapter]:
        return [NodeAdapter(n, self._page) for n in self._nodes]


class HtmlPage:
    def __init__(self, client: httpx.Client, base_url: str) -> None:
        self._client = client
        self._base_url = base_url.rstrip("/") + "/"
        self._url: str = self._base_url
        self._html: str = ""
        self._tree: Optional[HTMLParser] = None

    @property
    def url(self) -> str:
        return self._url

    def abs_url(self, href: str) -> str:
        return urljoin(self._url, href)

    def goto(self, url: str) -> None:
        full = urljoin(self._base_url, url)
        resp = self._client.get(full)
        self._url = str(resp.url)
        self._html = resp.text
        self._tree = HTMLParser(self._html)

    def safe_goto(self, url: str) -> None:
        if self._url.find(url) < 0:
            self.goto(url)

    def wait_for_selector(self, selector: str, timeout: int = 10000) -> None:  # no-op for httpx
        return None

    def wait_for_load_state(self, state: str = "networkidle") -> None:  # no-op
        return None

    def content(self) -> str:
        return self._html

    def locator(self, selector: str) -> Locator:
        assert self._tree is not None, "Page not loaded"
        nodes = self._tree.css(selector) or []
        return Locator(nodes, self)


class SigaaBrowser:
    def __init__(self, config: BrowserConfig) -> None:
        self._config = config
        self._client: Optional[httpx.Client] = None

    def ensure_started(self) -> None:
        if self._client is None:
            self._client = httpx.Client(base_url=self._config.base_url, follow_redirects=True)

    def new_page(self) -> HtmlPage:
        self.ensure_started()
        assert self._client is not None
        return HtmlPage(self._client, self._config.base_url)

    @property
    def request(self) -> RequestClient:
        self.ensure_started()
        assert self._client is not None
        return RequestClient(self._client)

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    @contextmanager
    def page(self) -> Iterator[HtmlPage]:
        p = self.new_page()
        try:
            yield p
        finally:
            pass
