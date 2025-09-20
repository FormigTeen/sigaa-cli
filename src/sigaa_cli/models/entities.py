from dataclasses import dataclass

@dataclass(frozen=True)
class Teacher:
    name: str

@dataclass(frozen=True)
class ActiveStudent:
    email: str
    name: str
    registration: str
    course_label: str
    image_url: str

@dataclass(frozen=True)
class ActiveTeacher(Teacher):
    email: str
    education: str
    department: str
    image_url: str


