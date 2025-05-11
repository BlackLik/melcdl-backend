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
    password: fields.PasswordField
    password_repeated: fields.PasswordField
    is_confirm: bool


class LoginSchema(BaseModel):
    login: fields.LoginField
    password: fields.PasswordField


class RefreshTokenResponseSchema(BaseModel):
    refresh: str


class AccessTokenResponseSchema(BaseModel):
    access: str


class AllTokenResponseSchema(RefreshTokenResponseSchema, AccessTokenResponseSchema):
    pass


class BaseTokenSchema(BaseModel):
    iat: int
    exp: int
    sub: str
    login: fields.LoginField


class RefreshTokenSchema(BaseTokenSchema):
    pass


class AccessTokenSchema(BaseTokenSchema):
    created_on: datetime
    updated_on: datetime
    is_confirm: bool
