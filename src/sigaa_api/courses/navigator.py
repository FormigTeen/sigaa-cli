from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from ..browser import SigaaBrowser, HtmlPage
from ..parser import Parser
from ..resources.file import SigaaFile


@dataclass
class FileLink:
    name: str
    url: str


class CourseSession:
    def __init__(self, browser: SigaaBrowser, parser: Parser) -> None:
        self._browser = browser
        self._parser = parser

    def _current_page(self) -> HtmlPage:
        return self._browser.new_page()

    def list_files(self) -> List[FileLink]:
        # Heurística: examina a página atual do curso por links de download comuns
        with self._browser.page() as p:
            links = p.locator('a[href]')
            items: List[FileLink] = []
            for i in range(links.count()):
                a = links.nth(i)
                href = a.get_attribute('href') or ''
                text = self._parser.remove_tags_html(a.inner_html() or '')
                low = href.lower()
                if any(k in low for k in ['download', 'arquivo', 'anexo', 'file', 'attachment']) or any(
                    low.endswith(ext) for ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.zip', '.rar', '.7z', '.mp4', '.mp3', '.png', '.jpg', '.jpeg', '.gif']
                ):
                    url = p.abs_url(href)
                    name = text.strip() or url.split('/')[-1]
                    items.append(FileLink(name=name, url=url))
            # Remove duplicados por URL
            dedup: dict[str, FileLink] = {}
            for it in items:
                dedup[it.url] = it
            return list(dedup.values())

    def download_files(self, dest_dir: Path) -> List[Path]:
        files = self.list_files()
        f = SigaaFile(self._browser)
        saved: List[Path] = []
        for fl in files:
            saved.append(f.download_get(fl.url, dest_dir))
        return saved


class CourseNavigator:
    def __init__(self, browser: SigaaBrowser, parser: Parser) -> None:
        self._browser = browser
        self._parser = parser

    def open_course_by_title(self, title: str) -> CourseSession:
        # Abre a lista de turmas e clica na que bater com o título
        with self._browser.page() as p:
            p.goto('/sigaa/portais/discente/turmas.jsf')
            rows = p.locator('table.listagem > tbody > tr')
            found: Optional[int] = None
            norm_title = title.strip().lower()
            for i in range(rows.count()):
                row = rows.nth(i)
                cell_title = self._parser.remove_tags_html(row.locator('td').nth(0).inner_html() or '')
                if cell_title.strip().lower() == norm_title:
                    found = i
                    break
            if found is None:
                raise ValueError('SIGAA: Curso não encontrado pelo título informado.')
            row = rows.nth(found)
            # Tenta extrair URL a partir de href direto; se não houver, tenta decodificar onclick
            href_loc = row.locator('td').nth(0).locator('a[href]')
            target_url: Optional[str] = None
            if href_loc.count() > 0:
                href = href_loc.nth(0).get_attribute('href')
                if href:
                    target_url = p.abs_url(href)
            if target_url is None:
                onclick_loc = row.locator('a[onclick]')
                if onclick_loc.count() > 0:
                    js = onclick_loc.nth(0).get_attribute('onclick') or ''
                    # heurística: tenta extrair URL entre aspas simples
                    import re
                    m = re.search(r"'(/[^']+)'", js)
                    if m:
                        target_url = p.abs_url(m.group(1))
            if not target_url:
                raise ValueError('SIGAA: Não foi possível determinar a URL da turma para abrir.')
            p.goto(target_url)
            # Retorna uma sessão de curso; chamadas subsequentes abrem nova página já com contexto HTTP.
            return CourseSession(self._browser, self._parser)
