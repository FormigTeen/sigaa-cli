from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from ..browser import SigaaBrowser
from ..parser import Parser
from ..types import Campus, ProgressCallback, TeacherResult


class SigaaSearch:
    def __init__(self, browser: SigaaBrowser, parser: Parser) -> None:
        self._browser = browser
        self._parser = parser

    def teacher(self) -> "SigaaSearchTeacher":
        return SigaaSearchTeacher(self._browser, self._parser)


class SigaaSearchTeacher:
    def __init__(self, browser: SigaaBrowser, parser: Parser) -> None:
        self._browser = browser
        self._parser = parser
        self._page = None

    def _load_search_page(self):
        if self._page is not None:
            return self._page
        page = self._browser.new_page()
        page.goto("/sigaa/public/docente/busca_docentes.jsf")
        self._page = page
        return page

    def get_campus_list(self) -> List[Campus]:
        page = self._load_search_page()
        options = page.locator("select#form\\:departamento > option")
        count = options.count()
        result: List[Campus] = []
        for i in range(count):
            opt = options.nth(i)
            name = self._parser.remove_tags_html(opt.text_content())
            value = (opt.get_attribute("value") or "").strip()
            result.append(Campus(name=name, value=value))
        return result

    def search(self, teacher_name: str, campus: Optional[Campus] = None) -> List[TeacherResult]:
        page = self._load_search_page()
        # Monta submissão JSF: precisa do javax.faces.ViewState
        form = page.locator("form[name='form']")
        vs = None
        if form.count() > 0:
            hidden = form.nth(0).locator("input[name='javax.faces.ViewState']")
            if hidden.count() > 0:
                vs = hidden.nth(0).get_attribute('value')
        dep_val = campus.value if campus is not None else "0"
        payload = {
            "form": "form",
            "form:nome": teacher_name,
            "form:departamento": dep_val,
            "form:buscar": "form:buscar",
        }
        if vs:
            payload["javax.faces.ViewState"] = vs
        # Envia POST para a mesma URL
        self._browser.request.post("/sigaa/public/docente/busca_docentes.jsf", data=payload)
        # Recarrega página (após POST, a mesma URL deve refletir resultados)
        page.goto("/sigaa/public/docente/busca_docentes.jsf")

        rows = page.locator("table.listagem > tbody > tr[class]")
        results: List[TeacherResult] = []
        for i in range(rows.count()):
            row = rows.nth(i)
            name = self._parser.remove_tags_html(row.locator("span.nome").inner_html())
            department = self._parser.remove_tags_html(row.locator("span.departamento").inner_html())
            href = row.locator("span.pagina > a").nth(0).get_attribute("href") or ""
            photo_src = row.locator("img").nth(0).get_attribute("src") or ""
            if href:
                page_url = page.abs_url(href)
            else:
                page_url = page.url
            profile_picture_url: Optional[str]
            if not photo_src or "no_picture.png" in photo_src:
                profile_picture_url = None
            else:
                profile_picture_url = page.abs_url(photo_src)

            tr = TeacherResult(
                name=name,
                department=department,
                page_url=str(page_url),
                profile_picture_url=profile_picture_url,
            )

            # Bind helpers
            def _get_email(page_url_local: str = str(page_url)) -> Optional[str]:
                with self._browser.page() as p:
                    p.goto(page_url_local)
                    # Busca por bloco #contato e varre labels
                    items = p.locator("#contato > *").all()
                    for item in items:
                        label = self._parser.remove_tags_html((item.locator("dt").nth(0).inner_html() if item.locator("dt").count() else ""))
                        if label == "Endereço eletrônico":
                            value_html = item.locator("dd").nth(0).inner_html() if item.locator("dd").count() else ""
                            value = self._parser.remove_tags_html(value_html)
                            if value and value != "não informado":
                                return value
                    return None

            def _download_profile_picture(basepath: Path, callback: Optional[ProgressCallback] = None, url: Optional[str] = profile_picture_url) -> Path:
                if not url:
                    raise ValueError("SIGAA: This teacher doesn't have profile picture")
                basepath.mkdir(parents=True, exist_ok=True)
                # Faz o download via request API do contexto
                req = self._browser.request
                resp = req.get(url)
                resp.raise_for_status()
                content = resp.body()
                total = len(content)
                if callback:
                    callback(total, total)
                # Nome do arquivo a partir da URL
                filename = url.split("/")[-1] or "photo.jpg"
                dest = basepath / filename
                dest.write_bytes(content)
                return dest

            object.__setattr__(tr, "get_email", _get_email)
            object.__setattr__(tr, "download_profile_picture", _download_profile_picture)
            results.append(tr)

        return results
