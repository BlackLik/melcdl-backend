from collections.abc import AsyncGenerator
from typing import Any

import httpx
import pytest

from internal.bootstrap.app import AppCommand


@pytest.fixture
async def async_client() -> AsyncGenerator[httpx.AsyncClient, Any]:
    transport = httpx.ASGITransport(app=AppCommand().get_app())
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
