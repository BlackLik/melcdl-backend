from sqlalchemy import Boolean, Column, String

from internal.utils.crypto import get_max_length_str_fernet, get_max_length_str_sha512

from .base import SoftModel, UUIDModel


class UserModel(UUIDModel, SoftModel):
    __tablename__ = "user"

    login = Column(String(length=get_max_length_str_fernet(256)), nullable=False)
    hash_login = Column(String(length=get_max_length_str_sha512()), nullable=False, index=True)
    password = Column(String(length=get_max_length_str_sha512()), nullable=False, index=True)
    is_confirm = Column(Boolean(), nullable=False)
