from sqlalchemy import Column, String

from internal.utils.crypto import get_max_length_str_fernet, get_max_length_str_sha512

from .base import SoftModel, UUIDModel


class UserModel(UUIDModel, SoftModel):
    __tablename__ = "user"

    email = Column(String(length=get_max_length_str_fernet(256)), nullable=False, index=True)
    password = Column(String(length=get_max_length_str_sha512()), nullable=False, index=True)
