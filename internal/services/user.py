from datetime import timedelta
from functools import lru_cache
from typing import Any

import jose
import pydantic
import sqlalchemy as sa
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from internal import config
from internal.entities import models, schemas
from internal.repositories.user import UserRepository
from internal.services.crypto import CryptoService
from internal.services.utime import TimeService
from internal.utils import errors, log
from internal.utils.auth import HTTPBearerAuth, HTTPBearerAuthConfig
from internal.utils.crypto import hash_string
from internal.utils.errors import UnauthorizedError, UniqueError, ValidationError

logger = log.get_logger()


class UserService:
    @classmethod
    async def create_new_user(
        cls,
        session: AsyncSession,
        create_user: schemas.user.CreateUserSchema,
    ) -> schemas.user.UserSchema:
        if not create_user.is_confirm:
            msg = "is_confirm must be True"
            raise ValidationError(detail=msg)

        if hash_string(create_user.password_repeated) != hash_string(create_user.password):
            msg = "password and password_repeated need be equal"
            raise ValidationError(detail=msg)

        user_repo = UserRepository(session=session)

        if await user_repo.filter(hash_login=hash_string(create_user.login), deleted_on=sa.null()):
            msg = "Login already use"
            raise UniqueError(detail=msg)

        user = await user_repo.create(
            login=CryptoService.encrypt(data=create_user.login).decode(),
            hash_login=hash_string(create_user.login),
            password=hash_string(create_user.password),
            is_confirm=create_user.is_confirm,
        )

        await session.commit()

        user.login = CryptoService.decrypt(user.login)

        return schemas.user.UserSchema.model_validate(user, from_attributes=True)

    @staticmethod
    def get_refresh_body(user: models.UserModel) -> schemas.user.RefreshTokenSchema:
        settings = config.get_config()
        iat_datetime = TimeService.get_datetime_now()
        exp_datetime = iat_datetime + timedelta(seconds=settings.JWT_EXPIRATION_REFRESH_SECONDS)

        return schemas.user.RefreshTokenSchema(
            iat=int(iat_datetime.timestamp()),
            exp=int(exp_datetime.timestamp()),
            sub=str(user.id),
            login=CryptoService.decrypt(user.login),
        )

    @staticmethod
    def get_access_body(user: models.UserModel) -> schemas.user.AccessTokenSchema:
        settings = config.get_config()
        iat_datetime = TimeService.get_datetime_now()
        exp_datetime = iat_datetime + timedelta(seconds=settings.JWT_EXPIRATION_ACCESS_SECONDS)
        return schemas.user.AccessTokenSchema(
            iat=int(iat_datetime.timestamp()),
            exp=int(exp_datetime.timestamp()),
            sub=str(user.id),
            login=CryptoService.decrypt(user.login),
            is_confirm=user.is_confirm,
            created_on=user.created_on.astimezone(TimeService.get_time_zone()),
            updated_on=user.created_on.astimezone(TimeService.get_time_zone()),
        )

    @staticmethod
    def encode_jwt(data: dict[str, Any]) -> str:
        settings = config.get_config()
        return jwt.encode(data, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    @staticmethod
    def _decode_jwt_jose(token: str) -> dict[str, Any]:
        settings = config.get_config()
        return jwt.decode(token=token, key=settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

    @classmethod
    def decode_jwt(cls, token: str) -> dict[str, Any]:
        if not cls.verify_jwt(token):
            raise UnauthorizedError(detail=None)
        return cls._decode_jwt_jose(token)

    @classmethod
    def decode_jwt_access_payload(cls, token: str) -> schemas.user.AccessTokenSchema:
        return schemas.user.AccessTokenSchema.model_validate(cls.decode_jwt(token=token))

    @classmethod
    def verify_jwt(cls, token: str) -> bool:
        try:
            cls._decode_jwt_jose(token)
        except jose.JWTError:
            return False

        return True

    @classmethod
    async def login(cls, data: schemas.user.LoginSchema, session: AsyncSession) -> schemas.user.AllTokenResponseSchema:
        user_repo = UserRepository(session=session)

        login_hash, password_hash = hash_string(data.login), hash_string(data.password)

        user = await user_repo.filter(hash_login=login_hash, deleted_on=sa.null(), password=password_hash)
        if user is None:
            raise errors.UnauthorizedError(detail=None)

        return schemas.user.AllTokenResponseSchema(
            access=cls.encode_jwt(cls.get_access_body(user).model_dump(mode="json")),
            refresh=cls.encode_jwt(cls.get_refresh_body(user).model_dump(mode="json")),
        )

    @classmethod
    async def refresh(
        cls,
        data: schemas.user.TokenResponseSchema,
        session: AsyncSession,
    ) -> schemas.user.AccessTokenResponseSchema:
        user_repo = UserRepository(session=session)

        refresh_token = schemas.user.RefreshTokenSchema.model_validate(cls.decode_jwt(data.token))

        user = await user_repo.filter(id=refresh_token.sub)
        if not user:
            raise errors.UnauthorizedError(detail=None)

        return schemas.user.AccessTokenResponseSchema(
            access=cls.encode_jwt(cls.get_access_body(user).model_dump(mode="json")),
        )

    @classmethod
    async def verify(
        cls,
        data: schemas.user.TokenResponseSchema,
        session: AsyncSession,
    ) -> schemas.user.VerifyResponseSchema:
        user_repo = UserRepository(session=session)
        if not cls.verify_jwt(data.token):
            return schemas.user.VerifyResponseSchema(verify=False)

        base_token = schemas.user.BaseTokenSchema.model_validate(cls.decode_jwt(data.token))

        user = await user_repo.filter(id=base_token.sub)
        if not user:
            return schemas.user.VerifyResponseSchema(verify=False)

        return schemas.user.VerifyResponseSchema(verify=True)

    @classmethod
    @lru_cache(maxsize=1)
    def get_bearer_auth(cls) -> HTTPBearerAuth:
        return HTTPBearerAuth(config=HTTPBearerAuthConfig(check_token=cls.check_token_access))

    @classmethod
    def check_token_access(cls, token: str) -> bool:
        if not cls.verify_jwt(token):
            return False

        try:
            schemas.user.AccessTokenSchema.model_validate(cls.decode_jwt(token))
        except pydantic.ValidationError:
            return False

        return True
