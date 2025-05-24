from datetime import datetime
from enum import Enum
from typing import Generic, TypeVar

from pydantic import UUID4, BaseModel

T = TypeVar("T")


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


class BasePaginatorSchema(BaseModel, Generic[T]):
    data: list[T]
    total_count: int
    total_pages: int
    batch_size: int
    current_page: int
