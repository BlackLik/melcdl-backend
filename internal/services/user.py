import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from internal.entities.schemas.user import CreateUserSchema, UserSchema
from internal.repositories.user import UserRepository
from internal.utils.crypto import hash_string
from internal.utils.errors import UniqueError, ValidationError
from tests.test_db import CryptoService


class UserService:
    @classmethod
    async def create_new_user(cls, session: AsyncSession, create_user: CreateUserSchema) -> UserSchema:
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

        return UserSchema.model_validate(user, from_attributes=True)
