from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import Request, Response

from internal.utils import log

from . import types

logger = log.get_logger()


def _exception_handler(
    err: type[types.BaseError],
    *,
    is_logger: bool = False,
) -> Callable[[Request, Any], Awaitable[Response]]:
    async def wrapper(_: Request, exc: Exception) -> Response:
        if is_logger:
            logger.exception("Error")

        raise err(status_code=None, detail=str(exc))

    return wrapper


def get_exception_handlers() -> dict[int | type[Exception], Callable[[Request, Any], Awaitable[Response]]]:
    return {
        ValueError: _exception_handler(types.ValidationError),
        KeyError: _exception_handler(types.NotFoundError),
        Exception: _exception_handler(types.InternalServerError, is_logger=True),
    }
