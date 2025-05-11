from datetime import datetime

from faker import Faker
from pytest_benchmark.fixture import BenchmarkFixture
from sqlalchemy.ext.asyncio import AsyncSession

from internal.entities.models import UserModel
from internal.services.crypto import CryptoService
from internal.utils import crypto


class TestUser:
    async def test_user_model_insert(self, fake: Faker, db_session: AsyncSession) -> None:
        """
        Unit test: создаём и сохраняем экземпляр UserModel без использования FastAPI.
        Проверяем, что атрибуты сохраняются и генерируется UUID.
        """

        test_login = fake.user_name()
        test_hash = crypto.hash_string(test_login)
        test_login = CryptoService.encrypt(test_login).decode()
        test_password = crypto.hash_string(fake.password(256))

        user = UserModel(
            login=test_login,
            hash_login=test_hash,
            password=test_password,
            is_confirm=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.id is not None, "UUID должен быть сгенерирован"
        assert user.login == test_login
        assert user.hash_login == test_hash
        assert user.password == test_password

        assert hasattr(user, "created_on"), "SoftModel: должен быть created_at"
        assert isinstance(user.created_on, datetime)
        assert user.deleted_on is None, "SoftModel: deleted_at по умолчанию None"

    async def test_benchmark_user_model_insert(
        self,
        benchmark: BenchmarkFixture,
        fake: Faker,
        db_session: AsyncSession,
    ) -> None:
        async def create_user() -> UserModel:
            test_login = fake.user_name()
            test_hash = crypto.hash_string(test_login)
            test_login = CryptoService.encrypt(test_login).decode()
            test_password = crypto.hash_string(fake.password(256))

            user = UserModel(
                login=test_login,
                hash_login=test_hash,
                password=test_password,
                is_confirm=True,
            )
            db_session.add(user)
            await db_session.commit()
            await db_session.refresh(user)
            return user

        benchmark.group = "database_user_model_insert"
        user = await benchmark(create_user)
        assert user.id is not None, "UUID должен быть сгенерирован"
