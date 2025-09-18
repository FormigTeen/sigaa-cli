import os
from typing import TypeVar, Optional
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(), override=False)

USER_KEY = "SIGAA_API_USER"
PASSWORD_KEY = "SIGAA_API_PASSWORD"
DEFAULT_PROVIDER_KEY = "SIGAA_API_DEFAULT_PROVIDER"
DATA_PATH = "SIGAA_API_DATA_PATH"

def get_config_if_none(key: str, value: Optional[str] = None, default_value: Optional[str] = None) -> Optional[str]:
    return value if value is not None else os.getenv(key) or default_value

def get_config(key: str, default_value: Optional[str] = None) -> Optional[str]:
    return os.getenv(key, default_value)