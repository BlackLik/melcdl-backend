from collections.abc import Callable

from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel


class HTTPBearerAuthConfig(BaseModel):
    bearer_format: str | None = None
    scheme_name: str | None = None
    description: str | None = None
    check_token: Callable[[str], bool] | None = None
    auto_error: bool = True


class HTTPBearerAuth(HTTPBearer):
    """
    OAuth2 flow for authentication using a bearer token obtained with an OAuth2 code
    flow. An instance of it would be used as a dependency.
    """

    def __init__(self, config: HTTPBearerAuthConfig) -> None:
        self.check_token = config.check_token
        super().__init__(
            bearerFormat=config.bearer_format,
            scheme_name=config.scheme_name,
            description=config.description,
            auto_error=config.auto_error,
        )

    def get_error(self) -> None:
        if self.auto_error:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authenticated")

    async def __call__(self, request: Request) -> None | str:
        data = await super().__call__(request)
        if not data:
            return None

        token = data.credentials
        if self.check_token and not self.check_token(token):
            return self.get_error()

        return token
