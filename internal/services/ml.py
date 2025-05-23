import math
import uuid

from async_lru import alru_cache
from botocore.exceptions import ClientError
from fastapi import UploadFile, status
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

from internal.config import get_config
from internal.config.s3 import get_s3_session
from internal.entities import schemas
from internal.repositories.ml import FilesRepository, TasksRepository
from internal.services.crypto import CryptoService
from internal.utils import errors, log
from internal.utils.errors.types import BadRequestError, InternalServerError

logger = log.get_logger()


class MLService:
    @staticmethod
    @alru_cache(maxsize=2, ttl=get_config().TTL_CACHE)
    async def check_bucket_exists(bucket_name: str) -> bool:
        session = get_s3_session()

        async with session.client("s3", endpoint_url=get_config().S3_URL) as s3:
            try:
                await s3.head_bucket(Bucket=bucket_name)

            except ClientError as e:
                error_code = int(e.response["Error"]["Code"])
                if error_code != status.HTTP_404_NOT_FOUND:
                    logger.exception("Error client")
                    raise

                await s3.create_bucket(Bucket=bucket_name)

        return True

    @classmethod
    async def upload_img(
        cls,
        user_id: UUID4,
        file: UploadFile,
        session: AsyncSession,
    ) -> schemas.ml.TaskCreateResponseSchema:
        if not file.content_type.startswith("image/"):
            raise BadRequestError(detail="INCORRECT_FILE_TYPE")

        settings = get_config()

        if not await cls.check_bucket_exists(settings.S3_BUCKET_NAME_FILE):
            raise InternalServerError(detail="ERROR S3")

        file_repo, task_repo = FilesRepository(session=session), TasksRepository(session=session)

        file_id = uuid.uuid4()

        file_name = f"{file_id!s}.{file.filename.split('.')[-1]}"

        file_path = f"{settings.S3_BUCKET_NAME_FILE}/{file_name}"

        async with get_s3_session().client("s3", endpoint_url=settings.S3_URL) as s3:
            await s3.upload_fileobj(file.file, settings.S3_BUCKET_NAME_FILE, file_name)

        file = await file_repo.create(
            id=file_id,
            original_name=CryptoService.encrypt(file.filename).decode(),
            user_id=user_id,
            s3_path=file_path,
            type_file=file.content_type,
        )
        task = await task_repo.create(file_id=file.id, status=schemas.ml.StatusEnum.UPLOAD)
        await session.commit()

        return schemas.ml.TaskCreateResponseSchema(
            id=task.id,
            status=task.status,
            created_on=task.created_on,
            updated_on=task.updated_on,
        )

    @classmethod
    async def get_list_tasks(
        cls,
        user_id: UUID4,
        session: AsyncSession,
        batch_size: int,
        current_page: int,
    ) -> schemas.base.BasePaginatorSchema[schemas.ml.TaskItemSchema]:
        task_repo = TasksRepository(session=session)
        params = {"user_id": user_id}

        result = await task_repo.list(limit=batch_size, offset=batch_size * (current_page - 1), **params)

        total_count = await task_repo.count(**params)

        total_pages = math.ceil(total_count / batch_size)

        return schemas.base.BasePaginatorSchema[schemas.ml.TaskItemSchema](
            data=[
                schemas.ml.TaskItemSchema(
                    id=elem.id,
                    created_on=elem.created_on,
                    updated_on=elem.updated_on,
                    status=elem.status,
                    message=elem.message,
                )
                for elem in result
            ],
            total_count=total_count,
            total_pages=total_pages,
            current_page=current_page,
            batch_size=batch_size,
        )

    @classmethod
    async def get_single_task(cls, user_id: UUID4, session: AsyncSession, pk: UUID4) -> schemas.ml.TaskResponseSchema:
        task_repo, file_repo = TasksRepository(session=session), FilesRepository(session=session)

        task = await task_repo.filter(id=pk, user_id=user_id)
        if not task:
            raise errors.NotFoundError(detail=None)

        file = await file_repo.get(pk=task.file_id)

        return schemas.ml.TaskResponseSchema(
            id=task.id,
            created_on=task.created_on,
            updated_on=task.updated_on,
            status=task.status,
            message=task.message,
            file=schemas.ml.FileSchema(
                id=file.id,
                created_on=file.created_on,
                updated_on=file.updated_on,
                original_name=CryptoService.decrypt(file.original_name),
                url=get_config().S3_URL + "/" + file.s3_path,
            )
            if file
            else None,
        )
