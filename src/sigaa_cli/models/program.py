from dataclasses import dataclass
from pydantic import BaseModel
from src.sigaa_cli.models.course import AnchoredCourse


class Program(BaseModel):
    title: str
    location: str
    program_type: str
    mode: str
    time_code: str

class DetailedProgram(Program):
    id_ref: str
    code: str
    courses: list[AnchoredCourse]
