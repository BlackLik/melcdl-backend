from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from internal.config.models import get_db
from internal.entities import schemas
from internal.services.user import UserService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register/")
async def create_user(
    data: schemas.user.CreateUserSchema,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> schemas.user.UserSchema:
    result = await UserService.create_new_user(session=session, create_user=data)
    return JSONResponse(
        content=result.model_dump(mode="json"),
        status_code=status.HTTP_201_CREATED,
    )


@router.post("/login/")
async def login(
    data: schemas.user.LoginSchema,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> schemas.user.AllTokenResponseSchema:
    return await UserService.login(data=data, session=session)


@router.post("/refresh/")
async def refresh_user(
    data: schemas.user.TokenResponseSchema,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> schemas.user.AccessTokenResponseSchema:
    return await UserService.refresh(data=data, session=session)


@router.post("/verify/")
async def verify_user_token(
    data: schemas.user.TokenResponseSchema,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> schemas.user.VerifyResponseSchema:
    return await UserService.verify(data=data, session=session)
