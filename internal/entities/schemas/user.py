from datetime import datetime

from pydantic import UUID4, BaseModel

from . import fields


class UserSchema(BaseModel):
    id: UUID4
    login: fields.LoginField
    created_on: datetime
    updated_on: datetime
    is_confirm: bool


class CreateUserSchema(BaseModel):
    login: fields.LoginField
    password: str
    password_repeated: str
    is_confirm: bool
