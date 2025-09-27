from __future__ import annotations
import os
import shelve
from typing import Any, Optional, TypeVar, TypedDict

from src.sigaa_cli.utils.config import DATA_PATH, get_config
from src.sigaa_cli.utils.time import unix_seconds_dt

T = TypeVar("T")


class Value(TypedDict):
    value: str
    ttl: int


CACHE_FOLDER = os.path.join(
    str(get_config(DATA_PATH, "/tmp/sigaa")),
    "cache",
)


def _cache_path(provider: str) -> str:
    os.makedirs(CACHE_FOLDER, exist_ok=True)
    return os.path.join(CACHE_FOLDER, provider.lower())


def get_cache(provider: str) -> shelve.Shelf[Any]:
    path = _cache_path(provider)
    return shelve.open(path, flag="c", writeback=False);

def remove_value(cache_entry: shelve.Shelf[Any], key: str) -> bool:
    cache_entry.pop(key, None)
    return True

def save_value(cache_entry: shelve.Shelf[Any], key: str, value: dict[str, Any], ttl: int = 0) -> bool:
    cache_entry[key] = {
        "ttl": unix_seconds_dt() + ttl,
        "value": value,
    }
    return True

def get_value(cache_entry: shelve.Shelf[Any], key: str) -> Any:
     cached_value : Value | None = cache_entry.get(key)
     if cached_value is None:
         remove_value(cache_entry, key)
         return None
     if int(cached_value.get("ttl", 0)) <= unix_seconds_dt():
         return None
     return cached_value["value"]
