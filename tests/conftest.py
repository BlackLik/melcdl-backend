import asyncio
from collections.abc import AsyncGenerator, Generator
from typing import Any

import httpx
import pytest
import pytest_asyncio
from faker import Faker
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from internal import config
from internal.bootstrap.app import AppCommand
from internal.entities.models import BaseModel


@pytest_asyncio.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, Any]:
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def engine() -> AsyncEngine:
    """
    Инициализируем async-движок и сбрасываем/создаём схему перед сессией.
    """
    engine = create_async_engine(config.get_config().TEST_DATABASE_URL, echo=False, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.drop_all)
        await conn.run_sync(BaseModel.metadata.create_all)
    return engine


@pytest_asyncio.fixture(scope="function")
async def db_session(engine: AsyncEngine) -> AsyncGenerator[AsyncSession, Any]:
    """
    Отдельная сессия на каждый тест. После выхода — откат.
    """
    async_session_local = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with async_session_local() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def async_client() -> AsyncGenerator[httpx.AsyncClient, Any]:
    transport = httpx.ASGITransport(app=AppCommand().fastapi_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture(scope="function", autouse=True)
async def clean_tables(engine: AsyncEngine) -> AsyncGenerator[None, Any]:
    """
    Перед тестом и после теста удаляем все записи из всех таблиц.

    engine — асинхронный движок из другой фикстуры.
    """
    async with engine.begin() as conn:
        # Пройдём по всем таблицам в порядке удаления зависимых FK
        for table in reversed(BaseModel.metadata.sorted_tables):
            await conn.execute(delete(table))

    yield

    async with engine.begin() as conn:
        for table in reversed(BaseModel.metadata.sorted_tables):
            await conn.execute(delete(table))


@pytest.fixture
def fake() -> Faker:
    return Faker("ru_RU")
