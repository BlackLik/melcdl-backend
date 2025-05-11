import httpx
from faker import Faker
from fastapi import status
from pytest_benchmark.fixture import BenchmarkFixture
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from internal.entities.models import UserModel
from internal.services.user import CreateUserSchema
from internal.utils.crypto import hash_string


class TestAuth:
    async def test_create_new_user_success(
        self,
        fake: Faker,
        async_client: httpx.AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        password = fake.password(length=6)
        create_user = CreateUserSchema(
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

        qs = select(UserModel).where(UserModel.hash_login == hash_string(data["login"]))

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
            create_user = CreateUserSchema(
                login=fake.user_name(),
                password=password,
                password_repeated=password,
                is_confirm=True,
            )

            return await async_client.post("/api/v1/auth/register/", json=create_user.model_dump())

        benchmark.group = "create_new_user_success"
        response = await benchmark(create_user)
        assert response.status_code == status.HTTP_201_CREATED
