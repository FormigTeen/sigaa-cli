from dataclasses import dataclass

from src.sigaa_api.models.entities import ActiveTeacher, ActiveStudent


@dataclass(frozen=True)
class Course:
    code: str
    name: str

@dataclass(frozen=True)
class ActiveCourse(Course):
    table_location: str
    time_codes: list[str]
    term: str
    class_code: str
    teachers: list[ActiveTeacher]
    students: list[ActiveStudent]
    total_classes: int
    number_classes: int