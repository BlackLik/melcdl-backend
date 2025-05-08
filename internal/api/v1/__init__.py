from fastapi import APIRouter

from internal.api import include_router

from . import auth, predict

router = APIRouter(prefix="/v1")
include_router(include_router=router, models=[auth, predict])
