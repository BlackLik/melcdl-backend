from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from internal.api.v1.auth import get_db
from internal.entities import schemas
from internal.services.ml import MLService
from internal.services.user import UserService

router = APIRouter(prefix="/ml", tags=["ML"])


@router.post("/upload/")
async def upload_image(
    token: Annotated[str, Depends(UserService.get_bearer_auth())],
    file: Annotated[UploadFile, File(...)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> schemas.ml.TaskCreateResponseSchema | dict[str, Any]:
    payload = UserService.decode_jwt_access_payload(token=token)

    return await MLService.upload_img(user_id=payload.sub, file=file, session=session)
