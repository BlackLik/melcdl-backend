import hashlib
from typing import AnyStr

from cryptography.fernet import Fernet


def get_max_length_str_fernet(num: int) -> int:
    return len(Fernet(Fernet.generate_key()).encrypt(("a" * num).encode()).decode())


def get_max_length_str_sha512() -> int:
    return len(hashlib.sha512(b"a").hexdigest())


def hash_string(data: AnyStr) -> str:
    """Хеширует строку при помощью SHA-512."""

    data_byte = data if isinstance(data, bytes) else data.encode()

    return hashlib.sha512(data_byte).hexdigest()
