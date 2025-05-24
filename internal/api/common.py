from fastapi import APIRouter

from internal.entities import schemas

router = APIRouter(tags=["common"])


@router.get("/health")
# @alru_cache(maxsize=1)
async def health_check() -> schemas.base.MessageSchema:
    return schemas.base.MessageSchema(message="OK")
