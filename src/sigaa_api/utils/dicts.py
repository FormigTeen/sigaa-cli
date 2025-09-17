from dataclasses import dataclass, asdict, is_dataclass, fields
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from uuid import UUID
from typing import Any

def to_jsonable(x: Any):
    if is_dataclass(x):
        # asdict já recursa em dataclasses; ainda assim tratamos tipos especiais
        return {k: to_jsonable(v) for k, v in asdict(x).items()}
    if isinstance(x, (datetime, date)):
        return x.isoformat()
    if isinstance(x, UUID):
        return str(x)
    if isinstance(x, Decimal):
        # escolha: str para precisão exata, ou float para aritmética
        return str(x)
    if isinstance(x, Enum):
        return x.value
    if isinstance(x, set):
        return [to_jsonable(v) for v in x]            # JSON não tem set
    if isinstance(x, tuple):
        return [to_jsonable(v) for v in x]            # JSON não tem tuple
    if isinstance(x, list):
        return [to_jsonable(v) for v in x]
    if isinstance(x, dict):
        return {k: to_jsonable(v) for k, v in x.items()}
    return x

def from_record(cls, data: dict):
    kwargs = {}
    for f in fields(cls):
        val = data.get(f.name, MISSING)
        if val is MISSING:
            continue
        t = f.type
        if t is datetime:
            val = datetime.fromisoformat(val)
        elif t is date:
            val = date.fromisoformat(val)
        elif t is UUID:
            val = UUID(val)
        elif t is set[str] or t is set:
            val = set(val)
        elif is_dataclass(t) and isinstance(val, dict):
            val = from_record(t, val)
        kwargs[f.name] = val
    return cls(**kwargs)