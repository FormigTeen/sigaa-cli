from __future__ import annotations
import os
import shelve
from typing import Any, Optional, TypeVar

from src.sigaa_cli.utils.config import DATA_PATH, get_config

T = TypeVar("T")


# Pasta base para arquivos de cache (por provedor)
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