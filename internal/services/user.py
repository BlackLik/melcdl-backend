from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from internal.entities.schemas.user import CreateUserSchema, UserSchema
from internal.repositories.user import UserRepository
from internal.utils.crypto import hash_string
from tests.test_db import CryptoService


class UserService:
    @classmethod
    async def create(cls, session: AsyncSession, create_user: CreateUserSchema) -> UserSchema:
        if not create_user.is_confirm:
            msg = "is_confirm must be True"
            raise ValueError(msg)

        if hash_string(create_user.password_repeated) != hash_string(create_user.password):
            msg = "password and password_repeated need be equal"
            raise ValidationError(msg)

        user_repo = UserRepository.get_repository(session=session)

        if user_exists := await user_repo.filter(hash_login=hash_string(create_user.login)):
            raise ValueError

        user = await user_repo.create(
            email=CryptoService.encrypt(create_user.login).decode(),
        )

        user.login = CryptoService.decrypt(user.login)

        return UserSchema.model_validate(user)
