from fastapi import APIRouter

from internal.utils.routers import include_router

from . import v1

router = APIRouter(prefix="/")
include_router(include_router=router, models=[v1])
