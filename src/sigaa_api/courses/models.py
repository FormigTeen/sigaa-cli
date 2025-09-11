from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Course:
    title: str
    code: Optional[str]
    period: Optional[str]
    schedule: Optional[str]
    number_of_students: Optional[int]
    open_js_trigger: Optional[str] = None  # raw onclick JS if available

