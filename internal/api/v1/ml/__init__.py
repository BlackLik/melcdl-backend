from fastapi import APIRouter

from internal.api import include_router

from . import models, tasks

router = APIRouter(prefix="/ml")

include_router(include_router=router, models=[models, tasks])
