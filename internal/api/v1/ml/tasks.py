from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, Path, Query, UploadFile, status
from fastapi.responses import JSONResponse
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

from internal.api.v1.auth import get_db
from internal.client.kafka.producer import KafkaProducer
from internal.config.kafka import get_kafka_producer_context
from internal.entities import schemas
from internal.services.ml import MLService
from internal.services.user import UserService

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.put("/{model_pk}/")
async def upload_image(
    token: Annotated[str, Depends(UserService.get_bearer_auth())],
    file: Annotated[UploadFile, File(...)],
    session: Annotated[AsyncSession, Depends(get_db)],
    model_pk: Annotated[UUID4, Path()],
    producer: Annotated[KafkaProducer, Depends(get_kafka_producer_context)],
) -> schemas.ml.TaskCreateResponseSchema | dict[str, Any]:
    payload = UserService.decode_jwt_access_payload(token=token)

    result = await MLService.upload_img(
        user_id=payload.sub,
        file=file,
        session=session,
        model_pk=model_pk,
        producer=producer,
    )

    return JSONResponse(
        content=result.model_dump(mode="json"),
        status_code=status.HTTP_201_CREATED,
    )


@router.get("/")
async def get_list_tasks(
    token: Annotated[str, Depends(UserService.get_bearer_auth())],
    session: Annotated[AsyncSession, Depends(get_db)],
    batch_size: Annotated[int, Query(gt=0, le=20000)] = 100,
    current_page: Annotated[int, Query(gt=0)] = 1,
) -> schemas.base.BasePaginatorSchema[schemas.ml.TaskItemSchema]:
    payload = UserService.decode_jwt_access_payload(token=token)
    return await MLService.get_list_tasks(
        user_id=payload.sub,
        session=session,
        batch_size=batch_size,
        current_page=current_page,
    )


@router.get("/{pk}/")
async def get_single_task(
    token: Annotated[str, Depends(UserService.get_bearer_auth())],
    session: Annotated[AsyncSession, Depends(get_db)],
    pk: Annotated[UUID4, Path()],
) -> schemas.ml.TaskResponseSchema:
    payload = UserService.decode_jwt_access_payload(token=token)
    return await MLService.get_single_task(user_id=payload.sub, session=session, pk=pk)
