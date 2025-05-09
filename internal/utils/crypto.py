import hashlib

from cryptography.fernet import Fernet


def get_max_length_str_fernet(num: int) -> int:
    return len(Fernet(Fernet.generate_key()).encrypt(("a" * num).encode()).decode())


def get_max_length_str_sha512() -> int:
    return len(hashlib.sha512(b"a").hexdigest())
