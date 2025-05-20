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
from internal.utils import log
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
