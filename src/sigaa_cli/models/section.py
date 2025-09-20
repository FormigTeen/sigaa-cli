from dataclasses import dataclass
from pydantic import BaseModel
from src.sigaa_cli.models.course import Course
from src.sigaa_cli.models.entities import ActiveTeacher, ActiveStudent
from src.sigaa_cli.models.program import Program


class Spot(BaseModel):
    program: Program
    seats_count: int
    seats_accepted: int

class BaseSection(BaseModel):
    course: Course
    term: str
    time_codes: list[str]
    location_table: str

class Section(BaseSection):
    mode: str

class DetailedSection(Section):
    id_ref: str
    teachers: list[str]
    seats_count: int
    seats_accepted: int
    seats_requested: int
    seats_rerequested: int
    spots_reserved: list[Spot]


class ActiveSection(BaseSection):
    location_table: str
    term: str
    class_code: str
    teachers: list[ActiveTeacher]
    students: list[ActiveStudent]
    total_classes: int
    number_classes: int
