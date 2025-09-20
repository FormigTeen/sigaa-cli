from typing import Optional


def add_uri(host: str, uri: Optional[str] = None) -> str:
    uri = uri or '/'
    return f'{host}{uri}'