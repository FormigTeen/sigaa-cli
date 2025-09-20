from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from ..browser import SigaaBrowser
from ..types import ProgressCallback


@dataclass
class SigaaFile:
    browser: SigaaBrowser

    def download_get(self, url: str, basepath: Path, callback: Optional[ProgressCallback] = None) -> Path:
        basepath.mkdir(parents=True, exist_ok=True)
        resp = self.browser.request.get(url)
        resp.raise_for_status()
        content = resp.body()
        total = len(content)
        if callback:
            callback(total, total)
        filename = url.split('/')[-1] or 'download.bin'
        dest = basepath / filename
        dest.write_bytes(content)
        return dest

    def download_post(self, url: str, post_values: Dict[str, str], basepath: Path, callback: Optional[ProgressCallback] = None) -> Path:
        basepath.mkdir(parents=True, exist_ok=True)
        resp = self.browser.request.post(url, data=post_values)
        resp.raise_for_status()
        content = resp.body()
        total = len(content)
        if callback:
            callback(total, total)
        filename = url.split('/')[-1] or 'download.bin'
        dest = basepath / filename
        dest.write_bytes(content)
        return dest
