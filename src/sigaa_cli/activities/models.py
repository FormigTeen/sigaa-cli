from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Activity:
    course_title: str
    type: str  # Questionário | Tarefa | Avaliação
    title: str
    date: datetime
    done: bool

