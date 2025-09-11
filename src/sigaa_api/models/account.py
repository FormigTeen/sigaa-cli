from typing import NamedTuple, Optional

class Account(NamedTuple):
    provider: str
    registration: str
    name: Optional[str]
    email: Optional[str]
    profile_picture_url: str