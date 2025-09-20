from dataclasses import dataclass
from pydantic import BaseModel
from typing import NamedTuple, Optional

class Account(BaseModel):
    provider: str
    registration: str
    program: Optional[str]
    name: Optional[str]
    email: Optional[str]
    profile_picture_url: str

