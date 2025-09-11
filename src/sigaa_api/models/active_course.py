from typing import NamedTuple


class ActiveCourse(NamedTuple):
    code: str
    name: str
    location: str
    time_code: str
    term: str