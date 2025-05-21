from enum import auto

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
