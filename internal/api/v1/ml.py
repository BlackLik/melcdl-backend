from typing import Any

from fastapi import APIRouter

from tests.conftest import UserService

router = APIRouter(prefix="/ml")


@router.get("/history/", dependencies=[UserService.get_bearer_auth()])
async def get_history() -> dict[str, Any]:
    return {}
