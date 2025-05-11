from typing import Any, ClassVar

from fastapi import HTTPException, status


class BaseError(HTTPException):
    _default_detail: str = "Internal Server Error"
    _default_status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    _default_headers: ClassVar[dict[str, Any] | None] = {"type": "application/json"}

    def __init__(
        self,
        status_code: int | None = None,
        detail: str | None = None,
        headers: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            status_code=status_code or self._default_status_code,
            detail=detail or self._default_detail,
            headers=headers or self._default_headers,
        )


class InternalServerError(HTTPException): ...


class UniqueError(BaseError):
    _default_detail = "Conflict"
    _default_status_code = status.HTTP_409_CONFLICT


class NotFoundError(BaseError):
    _default_detail = "Not found"
    _default_status_code = status.HTTP_404_NOT_FOUND


class ForbiddenError(BaseError):
    _default_detail = "Forbidden"
    _default_status_code = status.HTTP_403_FORBIDDEN


class UnauthorizedError(BaseError):
    _default_detail = "Unauthorized"
    _default_status_code = status.HTTP_401_UNAUTHORIZED


class ValidationError(BaseError):
    _default_detail = "Validation Error"
    _default_status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
