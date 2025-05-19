from typing import Annotated, Any

from aiobotocore.client import AioBaseClient
from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from internal.api.v1.auth import get_db
from internal.config import s3
from tests.conftest import UserService

router = APIRouter(prefix="/ml")


@router.get("/history/", dependencies=[UserService.get_bearer_auth()])
async def get_history() -> dict[str, Any]:
    return {}


@router.post("/upload/", dependencies=[UserService.get_bearer_auth()])
async def upload_image(
    file: Annotated[UploadFile, File(...)],
    session: Annotated[AsyncSession, Depends(get_db())],
    s3_session: Annotated[AioBaseClient, Depends(s3.get_s3_client)],
    background_tasks: Annotated[BackgroundTasks, BackgroundTasks()],
) -> dict[str, Any]:
    return {}
