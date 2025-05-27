from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String

from internal.utils.crypto import get_max_length_str_fernet

from .base import SoftModel, UUIDModel


class Models(UUIDModel, SoftModel):
    __tablename__ = "models"

    name = Column(String(length=256), nullable=False)
    s3_path = Column(String(), nullable=False)
    is_exists = Column(Boolean(), default=False, nullable=False)


class Files(UUIDModel, SoftModel):
    __tablename__ = "files"

    original_name = Column(String(length=get_max_length_str_fernet(256)), nullable=False)
    s3_path = Column(String(), nullable=False)
    type_file = Column(String(length=256), nullable=False)
    user_id = Column(ForeignKey("user.id"))


class Predicts(UUIDModel):
    __tablename__ = "predicts"

    file_id = Column(ForeignKey("files.id"))
    model_id = Column(ForeignKey("models.id"))
    result = Column(Integer(), nullable=False)
    probability = Column(Float(), nullable=False)


class Tasks(UUIDModel, SoftModel):
    __tablename__ = "tasks"

    file_id = Column(ForeignKey("files.id"))
    user_id = Column(ForeignKey("user.id"))
    predict_id = Column(ForeignKey("predicts.id"))
    message = Column(String(), nullable=False, default="")
    status = Column(String(256), nullable=False)
