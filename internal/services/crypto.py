from functools import lru_cache
from typing import AnyStr

from cryptography.fernet import Fernet

from internal import config


class CryptoService:
    @staticmethod
    @lru_cache(maxsize=1)
    def get_fernet_default() -> Fernet:
        return Fernet(key=config.get_config().CRYPTO_KEY)

    @classmethod
    def get_crypto_func(cls, crypto_function: Fernet | None = None) -> Fernet:
        return crypto_function or cls.get_fernet_default()

    @classmethod
    def encrypt(cls, data: AnyStr, *, crypto_function: Fernet | None = None) -> bytes:
        return cls.get_crypto_func(crypto_function).encrypt(data if isinstance(data, bytes) else data.encode())

    @classmethod
    def decrypt(cls, data: AnyStr, *, crypto_function: Fernet | None = None) -> str:
        return cls.get_crypto_func(crypto_function).decrypt(data if isinstance(data, bytes) else data.encode()).decode()
