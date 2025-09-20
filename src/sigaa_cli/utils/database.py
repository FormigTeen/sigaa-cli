from __future__ import annotations
from pydantic import BaseModel
import os
from typing import Any, List, Optional, NamedTuple, TypeVar
from tinydb import TinyDB, Query
from src.sigaa_cli.utils.config import DATA_PATH, get_config

# Arquivo temporário para persistência dos resultados do scraper (sempre TinyDB)
DB_PATH = os.environ.get("SECTIONS_DB_FILE", "/tmp/sections.json")
os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)

T = TypeVar("T")
V = TypeVar("V")

DB_FOLDER = os.path.join(
    str(get_config(DATA_PATH, "/tmp/sigaa")),
    "data"
)
def get_database(provider: str) -> TinyDB:
    database_path = os.path.join(DB_FOLDER, provider.lower() + ".json")
    os.makedirs(os.path.dirname(database_path) or ".", exist_ok=True)
    return TinyDB(database_path)

def dump(model: BaseModel) -> dict[str, V]:
    return model.model_dump(mode="json")

def load(cls: type[BaseModel], data: dict[T, V]) -> BaseModel:
    return cls.model_validate(data)