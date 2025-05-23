from enum import auto

from pydantic import HttpUrl

from . import base


class StatusEnum(base.BaseEnum):
    SUCCESS = auto()
    ERROR = auto()
    PREDICT = auto()
    UPLOAD = auto()


class TaskCreateResponseSchema(base.UUIDMixinSchema, base.CreatedMixinSchema, base.UpdatedMixinSchema):
    status: StatusEnum
    message: str = ""


class TaskItemSchema(base.UpdatedMixinSchema, base.CreatedMixinSchema, base.UUIDMixinSchema):
    status: StatusEnum
    message: str = ""


class FileSchema(base.UpdatedMixinSchema, base.CreatedMixinSchema, base.UUIDMixinSchema):
    url: HttpUrl
    original_name: str


class TaskResponseSchema(base.UpdatedMixinSchema, base.CreatedMixinSchema, base.UUIDMixinSchema):
    status: StatusEnum
    message: str = ""
    file: FileSchema | None = None
