from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from internal.config.models import get_db
from internal.entities import schemas
from internal.services.ml.base import MLService

router = APIRouter(prefix="/models", tags=["Models"])


@router.get("/")
async def get_models(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[schemas.ml.ModelSchema]:
    return await MLService.get_models(session=session)


@router.post("/")
async def predict_image(file: Annotated[UploadFile, File(...)]) -> dict[str, Any]:
    return await MLService.predict_image(file=file)
