from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from internal.config.models import get_db
from internal.entities import schemas
from internal.services.ml import MLService

router = APIRouter(prefix="/models", tags=["Models"])


@router.get("/")
async def get_models(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[schemas.ml.ModelSchema]:
    return await MLService.get_models(session=session)
