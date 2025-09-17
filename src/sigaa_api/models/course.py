from dataclasses import dataclass
from pydantic import BaseModel
from src.sigaa_api.models.entities import ActiveTeacher, ActiveStudent

class Course(BaseModel):
    code: str
    name: str

class DetailedCourse(Course):
    mode: str
    id_ref: str

class RequestedCourse(DetailedCourse):
    location: str
    prerequisites: list[list[str]]
    corequisites: list[list[str]]
    equivalences: list[list[str]]


class AnchoredCourse(DetailedCourse):
    program_code: str
    level: str
    type: str