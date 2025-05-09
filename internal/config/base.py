from enum import Enum
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings


class StandEnum(str, Enum):
    LOCAL = "LOCAL"
    PROD = "PROD"


class AppSettings(BaseSettings):
    HOST: str = "0.0.0.0"  # noqa: S104
    PORT: int = 8000

    MODE: StandEnum = StandEnum.LOCAL

    APP_WORKERS: int | None = None
    APP_RELOAD: bool = True

    APP_CONFIG_LOG: Path = "./config/logging.json"


@lru_cache(maxsize=1)
def get_config() -> AppSettings:
    return AppSettings()
