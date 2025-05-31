import io
import math
import uuid
from pathlib import Path
from typing import Any

from botocore.config import Config
from botocore.exceptions import ClientError
from fastapi import UploadFile, status
from PIL import Image
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

from internal.client.kafka.producer import KafkaProducer
from internal.config import get_config
from internal.config.models import get_async_session
from internal.config.s3 import get_s3_session
from internal.entities import models, schemas
from internal.repositories.ml import FilesRepository, ModelsRepository, PredictsRepository, TasksRepository
from internal.services.crypto import CryptoService
from internal.services.ml.model import PyTorchModel
from internal.utils import errors, log
from internal.utils.helper import async_log_error
from internal.utils.resnet_abcd_swin import ResNetCosineSwinModel

logger = log.get_logger()


class MLService:
    @classmethod
    async def upload_img(
        cls,
        user_id: UUID4,
        file: UploadFile,
        session: AsyncSession,
        model_pk: UUID4,
        producer: KafkaProducer,
    ) -> schemas.ml.TaskCreateResponseSchema:
        if not file.content_type.startswith("image/"):
            raise errors.BadRequestError(detail="INCORRECT_FILE_TYPE")

        settings = get_config()

        model_repo = ModelsRepository(session=session)

        model = await model_repo.get(pk=model_pk)
        if not model:
            raise errors.NotFoundError(detail="Not found model")

        file_repo, task_repo = FilesRepository(session=session), TasksRepository(session=session)

        file_id = uuid.uuid4()

        file_name = f"{settings.S3_DIR_NAME_FILE}/{file_id!s}.{file.filename.split('.')[-1]}"

        file_path = f"{settings.S3_CORE_BUCKET.rstrip('/')}/{file_name}"

        content = await file.read()
        if not content:
            # Либо файл был пустым, либо вы уже ранее его читали, и второй раз content будет пустым  # noqa: RUF003
            raise errors.BadRequestError(detail="Empty file body or already read")

        async with get_s3_session().client(
            "s3",
            endpoint_url=settings.S3_URL,
            config=Config(signature_version="s3v4"),
        ) as s3:
            await s3.put_object(
                Bucket=settings.S3_CORE_BUCKET,
                Key=file_name.strip("/"),
                Body=io.BytesIO(content),
            )

        file = await file_repo.create(
            id=file_id,
            original_name=CryptoService.encrypt(file.filename).decode(),
            user_id=user_id,
            s3_path=file_path,
            type_file=file.content_type,
        )
        task = await task_repo.create(file_id=file.id, status=schemas.ml.StatusEnum.UPLOAD, user_id=user_id)

        await session.commit()

        await producer.send(
            settings.KAFKA_TOPIC_MELANOMA_ML,
            schemas.ml.KafkaInputMessageSchema(task_id=task.id, model_id=model.id).model_dump_json(),
        )

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
        predict = await PredictsRepository(session=session).get(pk=task.predict_id)

        map_result = {
            schemas.ml.PredictEnum.MALIGNANT: "MALIGNANT",
            schemas.ml.PredictEnum.BENIGN: "BENIGN",
            schemas.ml.PredictEnum.ANOTHER: "ANOTHER",
        }

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
                url=get_config().S3_URL_PUBLIC + "/" + file.s3_path,
            )
            if file
            else None,
            predict=schemas.ml.PredictSchema(
                id=predict.id,
                result=map_result.get(predict.result, "ANOTHER"),
                probability=predict.probability,
            )
            if predict
            else None,
        )

    @classmethod
    async def get_internal_task(cls, session: AsyncSession, pk: UUID4) -> models.Tasks | None:
        task_repo = TasksRepository(session=session)

        return await task_repo.get(pk=pk)

    @classmethod
    async def update_internal_task(cls, session: AsyncSession, pk: UUID4, data: dict) -> models.Tasks:
        task_repo = TasksRepository(session=session)

        task = await task_repo.get(pk=pk)
        if not task:
            raise errors.NotFoundError(detail=None)

        await task_repo.update(obj=task, obj_in=data)

        await session.commit()

    @classmethod
    async def upload_model_default_to_bucket(cls) -> None:
        logger.info("Start upload model default to bucket")
        settings = get_config()

        dirs = settings.ML_DIR_TO_UPLOAD

        files = [f for f in dirs.iterdir() if f.is_file() and f.name.endswith((".pt", ".pth"))]

        logger.info("Find files: %s", files)

        async_session_local = get_async_session()

        async with (
            get_s3_session().client("s3", endpoint_url=get_config().S3_URL) as s3,
            async_session_local() as db_session,
        ):
            model_repo = ModelsRepository(session=db_session)
            for file in files:
                logger.info("Start upload %s to bucket", file.name)
                default_name_list = [
                    elem for elem in settings.ML_DEFAULT_NAME_TO_UPLOAD if elem["file_name"] == file.name
                ]
                default_name: dict[str, str] = default_name_list[0] if default_name_list else {}

                target_file = f"{settings.S3_DIR_NAME_MODEL}/{file.name}"
                s3_path = f"{settings.S3_CORE_BUCKET.rstrip('/')}/{target_file}"

                params_to_create = {
                    "name": default_name.get("model_name", file.stem.replace("_", " ").title()),
                    "s3_path": s3_path,
                    "is_exists": True,
                }
                try:
                    await s3.head_object(
                        Bucket=settings.S3_CORE_BUCKET,
                        Key=target_file,
                    )
                    logger.info("Model %s exists in bucket.", file.name)

                    await model_repo.get_or_create(
                        filters={"s3_path": s3_path},
                        params_to_create=params_to_create,
                    )

                    await db_session.commit()

                    continue
                except ClientError as e:
                    code = int(e.response["Error"]["Code"])
                    if code != status.HTTP_404_NOT_FOUND:
                        logger.exception("Error %s in S3", file.name)
                        raise

                try:
                    logger.info("%s download to s3...", file.name)
                    with file.open("rb") as data:
                        await s3.upload_fileobj(data, settings.S3_CORE_BUCKET, target_file)
                except ClientError:
                    logger.exception("Ошибка загрузки %s в S3", file.name)
                    raise

                await model_repo.create(**params_to_create)

                await db_session.commit()

        logger.info("End upload model default to bucket")

    @classmethod
    async def check_model_file_exists(cls) -> None:
        logger.info("Start check model file exists in bucket")
        settings = get_config()

        async_session_local = get_async_session()

        async with (
            get_s3_session().client("s3", endpoint_url=get_config().S3_URL) as s3,
            async_session_local() as db_session,
        ):
            model_repo = ModelsRepository(session=db_session)

            count_model = await model_repo.count()
            batch_size = settings.DEFAULT_BATCH_SIZE
            dir_ml = settings.ML_DIR_TO_UPLOAD

            for index in range(0, count_model, settings.DEFAULT_BATCH_SIZE):
                models = await model_repo.list(offset=index, limit=batch_size)
                for model in models:
                    bucket, key = model.s3_path.split("/", 1)
                    try:
                        await s3.head_object(Bucket=bucket, Key=key)
                        local_file = dir_ml / key

                        if not local_file.exists():
                            local_file.parent.mkdir(parents=True, exist_ok=True)
                            with local_file.open("wb") as f:
                                await s3.download_fileobj(Bucket=bucket, Key=key, Fileobj=f)

                        logger.info("Downloaded %s to %s", key, local_file.absolute())

                        await model_repo.update(model, {"is_exists": True})
                    except ClientError as e:
                        code = int(e.response["Error"]["Code"])
                        if code != status.HTTP_404_NOT_FOUND:
                            raise
                        await model_repo.update(model, {"is_exists": False})

                    await db_session.commit()

        logger.info("End check model file exists in bucket")

    @classmethod
    @async_log_error
    async def start_all_jobs(cls) -> None:
        await cls.upload_model_default_to_bucket()
        await cls.check_model_file_exists()

    @classmethod
    async def get_models(cls, session: AsyncSession) -> list[schemas.ml.ModelSchema]:
        model_repo = ModelsRepository(session=session)
        return [
            schemas.ml.ModelSchema(id=elem.id, name=elem.name)
            for index in range(0, await model_repo.count(), get_config().DEFAULT_BATCH_SIZE)
            for elem in await model_repo.list(offset=index, limit=get_config().DEFAULT_BATCH_SIZE)
        ]

    @classmethod
    async def get_model(cls, name_file: str) -> PyTorchModel:
        settings = get_config()
        file = settings.ML_DIR_TO_UPLOAD / name_file
        if file.exists():
            torch_model = PyTorchModel(model=ResNetCosineSwinModel())
            torch_model.load_model(file.absolute())
            return torch_model

        async with get_s3_session().client("s3", endpoint_url=get_config().S3_URL) as s3:
            with file.open("wb") as f:
                await s3.download_fileobj(
                    Bucket=settings.S3_CORE_BUCKET,
                    Key=f"{settings.S3_DIR_NAME_MODEL}/{name_file}",
                    Fileobj=f,
                )

        torch_model = PyTorchModel(model=ResNetCosineSwinModel())
        torch_model.load_model(file.absolute())

        return torch_model

    @staticmethod
    async def get_file(s3_path: str) -> bytes:
        bucket, key = s3_path.split("/", 1)
        async with get_s3_session().client("s3", endpoint_url=get_config().S3_URL) as s3:
            resp = await s3.get_object(Bucket=bucket, Key=key)
            body = resp["Body"]
            return await body.read()

    @classmethod
    async def predict_file(cls, session: AsyncSession, data: schemas.ml.KafkaInputMessageSchema) -> None:
        models_repo = ModelsRepository(session=session)
        tasks_repo = TasksRepository(session=session)
        files_repo = FilesRepository(session=session)
        predicts_repo = PredictsRepository(session=session)
        logger.info("Input data to predict %s", data.model_dump_json())

        task = await tasks_repo.get(pk=data.task_id)
        if not task:
            raise errors.NotFoundError(detail=None)

        model = await models_repo.filter(id=data.model_id, is_exists=True)
        if not model:
            raise errors.NotFoundError(detail=None)

        file = await files_repo.get(pk=task.file_id)
        if not file:
            raise errors.NotFoundError(detail=None)

        model_class = await cls.get_model(name_file=Path(model.s3_path).name)

        img = Image.open(io.BytesIO(await cls.get_file(file.s3_path))).convert("RGB")

        result, probability = model_class.predict(image_input=img)

        predict = await predicts_repo.create(file_id=file.id, model_id=model.id, result=result, probability=probability)
        await session.commit()

        await tasks_repo.update(task, {"status": schemas.ml.StatusEnum.SUCCESS, "predict_id": predict.id})
        await session.commit()

    @classmethod
    async def predict_image(cls, file: UploadFile) -> dict[str, Any]:
        model = await cls.get_model("resnet18_melanoma_with_abcd_swin.pth")

        result = model.predict(image_input=Image.open(io.BytesIO(await file.read())).convert("RGB"))
        return {"result": result}
