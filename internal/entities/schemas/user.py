from datetime import datetime

from pydantic import UUID4, BaseModel, ConfigDict

from . import fields


class UserSchema(BaseModel):
    id: UUID4
    login: fields.LoginField
    created_on: datetime
    updated_on: datetime
    is_confirm: bool

    model_config = ConfigDict(from_attributes=True)


class CreateUserSchema(BaseModel):
    login: fields.LoginField
    password: str
    password_repeated: str
    is_confirm: bool
