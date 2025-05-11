import asyncio
import logging
from collections.abc import AsyncGenerator, Generator
from typing import Any
from unittest.mock import Mock

import httpx
import pytest
import pytest_asyncio
from faker import Faker
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from internal import config
from internal.bootstrap.app import AppCommand
from internal.entities import models
from internal.services.crypto import CryptoService
from internal.services.user import UserService
from internal.utils.crypto import hash_string


@pytest.fixture(scope="session", autouse=True)
def setup_logging() -> None:
    logging.basicConfig(level=logging.WARNING)
    logging.getLogger("sqlalchemy.engine.Engine").disabled = True


@pytest_asyncio.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, Any]:
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def engine(session_mocker: Mock) -> AsyncEngine:
    """
    Инициализируем async-движок и сбрасываем/создаём схему перед сессией.
    """
    settings = config.get_config()
    settings.DATABASE_URL = settings.TEST_DATABASE_URL
    session_mocker.patch("internal.config.get_config", return_value=settings)

    engine = create_async_engine(settings.TEST_DATABASE_URL, echo=False, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(models.BaseModel.metadata.drop_all)
        await conn.run_sync(models.BaseModel.metadata.create_all)
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
        for table in reversed(models.BaseModel.metadata.sorted_tables):
            await conn.execute(delete(table))

    yield

    async with engine.begin() as conn:
        for table in reversed(models.BaseModel.metadata.sorted_tables):
            await conn.execute(delete(table))


@pytest.fixture
def fake() -> Faker:
    return Faker("ru_RU")


@pytest_asyncio.fixture(scope="function")
async def mock_user(fake: Faker, db_session: AsyncSession) -> AsyncGenerator[dict[str, Any], Any]:
    password = fake.password(6)
    login = fake.user_name()
    user = models.UserModel(
        login=CryptoService.encrypt(login).decode(),
        hash_login=hash_string(login),
        password=hash_string(password),
        is_confirm=True,
    )
    db_session.add(user)
    await db_session.commit()
    db_session.refresh(user)

    yield {
        "login": login,
        "password": password,
        "access": UserService.encode_jwt(UserService.get_access_body(user=user).model_dump(mode="json")),
        "refresh": UserService.encode_jwt(UserService.get_refresh_body(user).model_dump(mode="json")),
        "id": str(user.id),
    }

    db_session.delete(user)
    await db_session.commit()
