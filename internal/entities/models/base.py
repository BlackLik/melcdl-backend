import uuid

from sqlalchemy import UUID, Column, DateTime, func
from sqlalchemy.orm import DeclarativeBase


class BaseModel(DeclarativeBase):
    pass


class UUIDModel(BaseModel):
    __abstract__ = True

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class SoftModel(BaseModel):
    __abstract__ = True

    created_on = Column(DateTime, default=func.now())
    updated_on = Column(DateTime, default=func.now(), onupdate=func.now())
    deleted_on = Column(DateTime, nullable=True)
