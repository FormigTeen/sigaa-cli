from dataclasses import dataclass

from src.sigaa_api.models.course import AnchoredCourse


@dataclass(frozen=True)
class Program:
    code: str
    title: str

@dataclass(frozen=True)
class DetailedProgram(Program):
    location: str
    program_type: str
    mode: str
    time_code: str
    courses: list[AnchoredCourse]
