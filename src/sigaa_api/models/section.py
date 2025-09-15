from dataclasses import dataclass

from src.sigaa_api.models.course import Course
from src.sigaa_api.models.entities import ActiveTeacher, ActiveStudent
from src.sigaa_api.models.program import Program


@dataclass(frozen=True)
class Spot:
    program: Program
    seats_count: int
    seats_accepted: int

@dataclass(frozen=True)
class BaseSection:
    course: Course
    term: str
    time_codes: list[str]
    location_table: str

@dataclass(frozen=True)
class Section(BaseSection):
    mode: str

@dataclass(frozen=True)
class DetailedSection(Section):
    id_ref: str
    teachers: list[str]
    seats_count: int
    seats_accepted: int
    seats_requested: int
    seats_rerequested: int
    spots_reserved: list[Spot]


@dataclass(frozen=True)
class ActiveSection(BaseSection):
    location_table: str
    term: str
    class_code: str
    teachers: list[ActiveTeacher]
    students: list[ActiveStudent]
    total_classes: int
    number_classes: int
