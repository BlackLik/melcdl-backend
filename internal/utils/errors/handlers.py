from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import Request, Response

from . import types


def _exception_handler(err: type[types.BaseError]) -> Callable[[Request, Any], Awaitable[Response]]:
    async def wrapper(request: Request, exc: Exception) -> Response:  # noqa: ARG001
        raise err

    return wrapper


def get_exception_handlers() -> dict[int | type[Exception], Callable[[Request, Any], Awaitable[Response]]]:
    return {
        ValueError: _exception_handler(types.ValidationError),
        KeyError: _exception_handler(types.NotFoundError),
        Exception: _exception_handler(types.InternalServerError),
    }
