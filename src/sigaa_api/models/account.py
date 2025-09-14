from dataclasses import dataclass
from typing import NamedTuple, Optional

@dataclass(frozen=True) 
class Account:
    provider: str
    registration: str
    program: Optional[str]
    name: Optional[str]
    email: Optional[str]
    profile_picture_url: str

