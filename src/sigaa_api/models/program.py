from dataclasses import dataclass

from src.sigaa_api.models.course import AnchoredCourse


@dataclass(frozen=True)
class Program:
    title: str
    time_code: str
    location: str
    program_type: str
    mode: str

@dataclass(frozen=True)
class DetailedProgram(Program):
    code: str
    courses: list[AnchoredCourse]
