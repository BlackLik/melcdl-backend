from fastapi import APIRouter

from internal.entities import schemas

router = APIRouter(tags=["common"])


@router.get("/health")
async def health_check() -> schemas.base.MessageSchema:
    return schemas.base.MessageSchema(message="OK")
