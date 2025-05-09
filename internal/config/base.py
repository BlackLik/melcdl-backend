from functools import lru_cache

from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    HOST: str = "0.0.0.0"  # noqa: S104
    PORT: int = 8000

    APP_WORKERS: int | None = None
    APP_RELOAD: bool = True


@lru_cache(maxsize=1)
def get_config() -> AppSettings:
    return AppSettings()
