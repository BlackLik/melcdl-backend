from collections.abc import AsyncGenerator
from functools import lru_cache

import aioboto3
from aiobotocore.client import AioBaseClient

from .base import get_config


@lru_cache(maxsize=1)
def get_s3_session() -> aioboto3.Session:
    settings = get_config()
    return aioboto3.Session(
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
    )


async def get_s3_client() -> AsyncGenerator[AioBaseClient]:
    settings = get_config()
    session = get_s3_session()
    async with session.client("s3", endpoint_url=settings.S3_URL) as client:
        yield client
