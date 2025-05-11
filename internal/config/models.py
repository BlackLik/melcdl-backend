from collections.abc import AsyncGenerator
from functools import lru_cache
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.asyncio.engine import AsyncEngine

from . import get_config


@lru_cache(maxsize=1)
def get_engine() -> AsyncEngine:
    return create_async_engine(
        url=get_config().DATABASE_URL,
        echo=True,
        future=True,
    )


@lru_cache(maxsize=1)
def get_async_session() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=get_engine(),
        expire_on_commit=False,
        class_=AsyncSession,
    )


async def get_db() -> AsyncGenerator[AsyncSession, Any]:
    async_session_local = get_async_session()
    async with async_session_local() as session:
        yield session
