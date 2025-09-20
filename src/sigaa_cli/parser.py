from __future__ import annotations

import html
import re
from typing import Final


class Parser:
    _remove_tags: Final[tuple[str, ...]] = ("span", "em", "b", "i", "strong")

    def remove_tags_html(self, text: str | None) -> str:
        if not text:
            return ""
        try:
            new_text = text
            for tag in self._remove_tags:
                new_text = re.sub(rf"</?{tag}( [^>]+)?>", "", new_text, flags=re.IGNORECASE)

            new_text = re.sub(r"\n|\xA0|\t", " ", new_text)
            new_text = re.sub(r"</li>|</p>|<br\s*/?>", "\n", new_text, flags=re.IGNORECASE)

            # Remove quaisquer tags restantes
            while re.search(r"<[^>]+>", new_text):
                new_text = re.sub(r"<[^>]+>", " ", new_text)

            new_text = html.unescape(new_text)
            new_text = re.sub(r"\s+", " ", new_text)
            new_text = new_text.strip()
            # Normaliza quebras de linha repetidas
            new_text = re.sub(r"\n+", "\n", new_text)
            return new_text
        except Exception:
            return ""

