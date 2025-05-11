from typing import Any

import httpx
from faker import Faker
from fastapi import status
from pytest_benchmark.fixture import BenchmarkFixture
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from internal.entities import models, schemas
from internal.services.user import UserService
from internal.utils import log
from internal.utils.crypto import hash_string

logger = log.get_logger()


class TestAuth:
    async def test_create_new_user_success(
        self,
        fake: Faker,
        async_client: httpx.AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        password = fake.password(length=6)
        create_user = schemas.user.CreateUserSchema(
            login=fake.user_name(),
            password=password,
            password_repeated=password,
            is_confirm=True,
        )

        response = await async_client.post("/api/v1/auth/register/", json=create_user.model_dump())
        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()
        assert data["login"] == create_user.login
        assert "password" not in data
        assert "is_confirm" in data
        assert data["is_confirm"] == create_user.is_confirm

        qs = select(models.UserModel).where(models.UserModel.hash_login == hash_string(data["login"]))

        result = await db_session.execute(qs)
        user = result.scalar_one_or_none()
        assert user is not None

    async def test_benchmark_create_new_user_success(
        self,
        benchmark: BenchmarkFixture,
        fake: Faker,
        async_client: httpx.AsyncClient,
    ) -> None:
        async def create_user() -> httpx.Response:
            password = fake.password(length=6)
            create_user = schemas.user.CreateUserSchema(
                login=fake.user_name(),
                password=password,
                password_repeated=password,
                is_confirm=True,
            )

            return await async_client.post("/api/v1/auth/register/", json=create_user.model_dump())

        benchmark.group = "create_new_user"
        response = await benchmark(create_user)
        assert response.status_code == status.HTTP_201_CREATED

    async def test_login_user_success(
        self,
        async_client: httpx.AsyncClient,
        mock_user: dict[str, Any],
    ) -> None:
        data = schemas.user.LoginSchema(
            login=mock_user["login"],
            password=mock_user["password"],
        )
        response = await async_client.post("/api/v1/auth/login/", json=data.model_dump(mode="json"))
        assert response.status_code == status.HTTP_200_OK

        result = response.json()

        assert "access" in result
        assert "refresh" in result

    async def test_benchmark_login_user_success(
        self,
        benchmark: BenchmarkFixture,
        async_client: httpx.AsyncClient,
        mock_user: dict[str, Any],
    ) -> None:
        async def login() -> httpx.Response:
            data = schemas.user.LoginSchema(
                login=mock_user["login"],
                password=mock_user["password"],
            )
            return await async_client.post("/api/v1/auth/login/", json=data.model_dump(mode="json"))

        benchmark.group = "login_user"
        response = await benchmark(login)
        assert response.status_code == status.HTTP_200_OK

    async def test_login_user_unsuccess(
        self,
        fake: Faker,
        async_client: httpx.AsyncClient,
        mock_user: dict[str, Any],
    ) -> None:
        data = schemas.user.LoginSchema(
            login=mock_user["login"],
            password=fake.password(6),
        )
        response = await async_client.post("/api/v1/auth/login/", json=data.model_dump(mode="json"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_benchmark_login_user_unsuccess(
        self,
        fake: Faker,
        benchmark: BenchmarkFixture,
        async_client: httpx.AsyncClient,
        mock_user: dict[str, Any],
    ) -> None:
        async def login() -> httpx.Response:
            data = schemas.user.LoginSchema(
                login=mock_user["login"],
                password=fake.password(6),
            )
            return await async_client.post("/api/v1/auth/login/", json=data.model_dump(mode="json"))

        benchmark.group = "login_user"
        response = await benchmark(login)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_refresh_user_success(
        self,
        async_client: httpx.AsyncClient,
        mock_user: dict[str, Any],
    ) -> None:
        data = schemas.user.TokenResponseSchema(token=mock_user["refresh"])
        response = await async_client.post("/api/v1/auth/refresh/", json=data.model_dump())
        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert "access" in result
        assert UserService.verify_jwt(result["access"])
