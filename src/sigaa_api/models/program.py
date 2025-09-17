from dataclasses import dataclass
from pydantic import BaseModel
from src.sigaa_api.models.course import AnchoredCourse


class Program(BaseModel):
    title: str
    time_code: str
    location: str
    program_type: str
    mode: str

class DetailedProgram(Program):
    code: str
    courses: list[AnchoredCourse]
