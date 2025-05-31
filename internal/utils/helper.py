from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any

from internal.utils import log

logger = log.get_logger()


def async_log_error(func: Callable[..., Awaitable[Any]]):  # noqa: ANN201
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
        try:
            return await func(*args, **kwargs)
        except Exception:
            logger.exception("Error")
            raise

    return wrapper
