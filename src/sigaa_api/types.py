from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Optional


class LoginStatus(Enum):
    UNAUTHENTICATED = "unauthenticated"
    AUTHENTICATED = "authenticated"


class Institution(str, Enum):
    UFBA = "UFBA"


# Progress callback: total size and downloaded bytes (optional)
ProgressCallback = Callable[[int, Optional[int]], None]


@dataclass(frozen=True)
class Campus:
    name: str
    value: str


@dataclass
class TeacherResult:
    name: str
    department: str
    page_url: str
    profile_picture_url: Optional[str] = None

    # Methods filled by the search layer at runtime (bound methods)
    get_email: Callable[[], str | None] | None = None
    download_profile_picture: Callable[[Path, Optional[ProgressCallback]], Path] | None = None
