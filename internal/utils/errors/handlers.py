from collections.abc import Awaitable, Callable
from types import CoroutineType
from typing import Any

from fastapi import Request, Response

from . import BaseError, types


def _exception_handler(err: type[BaseError]) -> Callable[..., CoroutineType[Any, Any, Response]]:
    async def wrapper(_: Request, _: Exception) -> Response:
        raise err

    return wrapper


def get_exception_handlers() -> dict[int | type[Exception], Callable[[Request, Any], Awaitable[Response]]]:
    return {
        ValueError: _exception_handler(types.ValidationError),
        KeyError: _exception_handler(types.NotFoundError),
        Exception: _exception_handler(types.InternalServerError),
    }
