from __future__ import annotations

from dataclasses import dataclass
from .types import LoginStatus, Institution


@dataclass
class Session:
    institution: Institution
    login_status: LoginStatus = LoginStatus.UNAUTHENTICATED

