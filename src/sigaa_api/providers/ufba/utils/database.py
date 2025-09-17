from __future__ import annotations
from pydantic import BaseModel
import os
from typing import Any, List, Optional, NamedTuple, TypeVar
from tinydb import TinyDB, Query

from src.sigaa_api.browser import SigaaBrowser

# Arquivo temporário para persistência dos resultados do scraper (sempre TinyDB)
DB_PATH = os.environ.get("SECTIONS_DB_FILE", "/tmp/sections.json")
os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)

T = TypeVar("T")
V = TypeVar("V")


# Tipos locais (espelho de utils.detail_section) para reconstrução ao ler do DB
Spot = NamedTuple('Spot', [
    ('course', str),
    ('count', str)
])

Section = NamedTuple('Section', [
    ('ref_id', str),
    ('title', str),
    ('term', str),
    ('teachers', list[str]),
    ('mode', str),
    ('time_id', str),
    ('location', str),
    ('spots', list[Spot]),
    ('total', str),
    ('total_requested', str),
    ('total_accepted', str),
])


def _to_dict(obj: Any) -> Any:
    # Converte NamedTuple (Section/Spot) e listas aninhadas para dict/list serializável
    if hasattr(obj, "_asdict"):
        d = obj._asdict()
        return {k: _to_dict(v) for k, v in d.items()}
    if isinstance(obj, list):
        return [_to_dict(x) for x in obj]
    return obj

_db = TinyDB(DB_PATH)
_table = _db.table("sections")


def was_saved(id: str) -> bool:
    if not id:
        return False
    SectionQ = Query()
    return _table.get(SectionQ.ref_id == id) is not None


def save_detail_section(section: Any) -> None:
    data = _to_dict(section)
    # Garante que temos um ref_id para indexar
    ref_id = str(data.get("ref_id", "")) if isinstance(data, dict) else ""
    if not ref_id:
        return
    SectionQ = Query()
    _table.upsert(data, SectionQ.ref_id == ref_id)
    try:
        print(f"[DB] Salvo section ref_id={ref_id}")
    except Exception:
        pass

DB_FOLDER = os.path.join("/tmp", "sigaa", "data")
_connections = dict()
def get_database(provider: str) -> TinyDB:
    if provider not in _connections:
        database_path = os.path.join(DB_FOLDER, provider.lower() + ".json")
        os.makedirs(os.path.dirname(database_path) or ".", exist_ok=True)
        _connections[provider] = TinyDB(database_path)
    return _connections[provider]


def dump(model: BaseModel) -> dict[str, V]:
    return model.model_dump(mode="json")

def load(cls: type[BaseModel], data: dict[T, V]) -> BaseModel:
    return cls.model_validate(data)