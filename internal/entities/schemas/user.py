from datetime import datetime
from typing import Annotated

from pydantic import UUID4, BaseModel, ConfigDict, Field


class UserSchema(BaseModel):
    id: UUID4
    login: Annotated[str, Field(min_length=6, max_length=256)]
    created_on: datetime
    updated_on: datetime
    deleted_on: datetime | None
    is_confirm: bool

    model_config = ConfigDict(from_attributes=True)


class CreateUserSchema(BaseModel):
    login: Annotated[str, Field(min_length=6, max_length=256)]
    password: str
    password_repeated: str
    is_confirm: bool
