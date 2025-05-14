from enum import Enum
from functools import lru_cache
from multiprocessing import cpu_count
from pathlib import Path
from typing import Any

from pydantic import ValidationError, field_validator
from pydantic_settings import BaseSettings


class StandEnum(str, Enum):
    LOCAL = "LOCAL"
    PROD = "PROD"


class AppSettings(BaseSettings):
    APP_NAME: str = "melcdl-backend"
    APP_VERSION: str = "0.1.0"

    HOST: str = "0.0.0.0"  # noqa: S104
    PORT: int = 8000

    MODE: StandEnum = StandEnum.PROD

    APP_WORKERS: int = cpu_count()
    APP_RELOAD: bool = False

    APP_CONFIG_LOG: Path = "./config/logging.json"

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: str
    POSTGRES_DB: str
    DATABASE_URL: str
    TEST_DATABASE_URL: str = ""

    CRYPTO_KEY: str

    TZ_NAME: str = "UTC"

    JWT_EXPIRATION_REFRESH_SECONDS: int = 60 * 60 * 24 * 7
    JWT_EXPIRATION_ACCESS_SECONDS: int = 60 * 60 * 10
    JWT_ALGORITHM: str = "HS256"
    JWT_SECRET_KEY: str

    S3_URL: str
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str

    # kafka
    KAFKA_BOOTSTRAP_SERVERS: str
    KAFKA_GROUP_ID: str = APP_NAME

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def validate_postgres_url(cls, value: str | None = None, values: dict[str, Any] | None = None) -> str:
        if value:
            return value

        if not values:
            raise ValidationError

        return f"postgresql+asyncpg://{values['POSTGRES_USER']}:{values['POSTGRES_PASSWORD']}@{values['POSTGRES_HOST']}:{values['POSTGRES_PORT']}/{values['POSTGRES_DB']}"


@lru_cache(maxsize=1)
def get_config() -> AppSettings:
    return AppSettings()
