from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Union


@dataclass(frozen=True)
class StudentBond:
    registration: str
    program: str
    switch_url: Optional[str] = None


@dataclass(frozen=True)
class TeacherBond:
    pass


BondType = Union[StudentBond, TeacherBond]

