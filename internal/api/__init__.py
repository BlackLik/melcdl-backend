from fastapi import APIRouter

from internal.utils.routers import include_router

from . import common, kafka, v1

router = APIRouter(prefix="/api")
include_router(include_router=router, models=[v1, common])

__all__ = ["kafka", "router"]
