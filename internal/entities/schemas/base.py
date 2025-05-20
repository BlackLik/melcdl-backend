from datetime import datetime
from enum import Enum

from pydantic import UUID4, BaseModel


class MessageSchema(BaseModel):
    message: str


class CreatedMixinSchema(BaseModel):
    created_on: datetime


class UpdatedMixinSchema(BaseModel):
    updated_on: datetime


class DeletedMixinSchema(BaseModel):
    deleted_on: datetime | None = None


class UUIDMixinSchema(BaseModel):
    id: UUID4


class BaseEnum(str, Enum):
    @staticmethod
    def _generate_next_value_(name: str, start: str, count: int, last_values: str) -> str:  # noqa: ARG004
        return name
