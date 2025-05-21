import uuid
from typing import Any

import httpx
from faker import Faker
from fastapi import status
from pytest_benchmark.fixture import BenchmarkFixture
from sqlalchemy.ext.asyncio import AsyncSession

from internal.entities import models
from internal.entities.schemas.ml import StatusEnum
from internal.services.crypto import CryptoService


class TestMLTasks:
    async def test_get_tasks(
        self,
        fake: Faker,
        async_client: httpx.AsyncClient,
        db_session: AsyncSession,
        mock_user: dict[str, Any],
    ) -> None:
        file_id = uuid.uuid4()
        original_name = fake.file_name(category="image")
        type_file = original_name.split(".")[-1]
        file = models.Files(
            id=file_id,
            original_name=CryptoService.encrypt(fake.file_name(category="image")).decode(),
            s3_path=f"data/{file_id!s}.{type_file}",
            type_file=type_file,
            user_id=mock_user["id"],
        )
        db_session.add(file)
        await db_session.flush()
        task = models.Tasks(
            file_id=file.id,
            user_id=mock_user["id"],
            status=StatusEnum.UPLOAD,
        )
        db_session.add(task)
        await db_session.flush()
        await db_session.commit()

        params = {
            "batch_size": 100,
            "current_page": 1,
        }

        response = await async_client.get(
            "/api/v1/ml/tasks/",
            params=params,
            headers={"Authorization": f"Bearer {mock_user['access']}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        for field in ["total_count", "total_pages", "current_page", "batch_size", "data"]:
            assert field in data

        assert len(data["data"]) == 1

    async def test_benchmark_verify_access_user_success(
        self,
        fake: Faker,
        benchmark: BenchmarkFixture,
        async_client: httpx.AsyncClient,
        db_session: AsyncSession,
        mock_user: dict[str, Any],
    ) -> None:
        file_id = uuid.uuid4()
        original_name = fake.file_name(category="image")
        type_file = original_name.split(".")[-1]
        file = models.Files(
            id=file_id,
            original_name=CryptoService.encrypt(fake.file_name(category="image")).decode(),
            s3_path=f"data/{file_id!s}.{type_file}",
            type_file=type_file,
            user_id=mock_user["id"],
        )
        db_session.add(file)
        await db_session.flush()
        task = models.Tasks(
            file_id=file.id,
            user_id=mock_user["id"],
            status=StatusEnum.UPLOAD,
        )
        db_session.add(task)
        await db_session.flush()
        await db_session.commit()

        params = {
            "batch_size": 100,
            "current_page": 1,
        }

        async def get_tasks() -> httpx.Response:
            return await async_client.get(
                "/api/v1/ml/tasks/",
                params=params,
                headers={"Authorization": f"Bearer {mock_user['access']}"},
            )

        benchmark.group = "get_tasks"
        response = await benchmark(get_tasks)
        assert response.status_code == status.HTTP_200_OK

    async def test_get_task_upload(
        self,
        fake: Faker,
        async_client: httpx.AsyncClient,
        db_session: AsyncSession,
        mock_user: dict[str, Any],
    ) -> None:
        file_id = uuid.uuid4()
        original_name = fake.file_name(category="image")
        type_file = original_name.split(".")[-1]
        file = models.Files(
            id=file_id,
            original_name=CryptoService.encrypt(fake.file_name(category="image")).decode(),
            s3_path=f"data/{file_id!s}.{type_file}",
            type_file=type_file,
            user_id=mock_user["id"],
        )
        db_session.add(file)
        await db_session.flush()
        task = models.Tasks(
            file_id=file.id,
            user_id=mock_user["id"],
            status=StatusEnum.UPLOAD,
        )
        db_session.add(task)
        await db_session.flush()
        await db_session.commit()

        response = await async_client.get(
            f"/api/v1/ml/tasks/{task.id!s}/",
            headers={"Authorization": f"Bearer {mock_user['access']}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        for field in ["id", "created_on", "updated_on", "status", "message", "file"]:
            assert field in data

        assert data["file"] is not None
