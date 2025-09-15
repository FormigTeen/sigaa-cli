from dataclasses import dataclass

from src.sigaa_api.models.entities import ActiveTeacher, ActiveStudent

@dataclass(frozen=True)
class Course:
    code: str
    name: str

@dataclass(frozen=True)
class DetailedCourse(Course):
    mode: str
    id_ref: str

@dataclass(frozen=True)
class AnchoredCourse(DetailedCourse):
    program_code: str
    level: str
    type: str