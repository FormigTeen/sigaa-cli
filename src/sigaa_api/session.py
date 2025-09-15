from __future__ import annotations

from dataclasses import dataclass
from .types import LoginStatus


@dataclass
class Session:
    institution: str
    login_status: LoginStatus = LoginStatus.UNAUTHENTICATED

