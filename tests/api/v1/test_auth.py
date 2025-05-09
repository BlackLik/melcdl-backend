import httpx
from fastapi import status
from pytest_benchmark.fixture import BenchmarkFixture


class TestAuth:
    async def test_login_success(self, async_client: httpx.AsyncClient) -> None:
        response = await async_client.post("/api/v1/auth/login")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert data["message"] == "Login successful"

    async def test_benchmark_login_success(self, benchmark: BenchmarkFixture, async_client: httpx.AsyncClient) -> None:
        async def login() -> httpx.Response:
            return await async_client.post("/api/v1/auth/login")

        response = await benchmark(login)
        assert response.status_code == status.HTTP_200_OK

    async def test_logout_success(self, async_client: httpx.AsyncClient) -> None:
        response = await async_client.post("/api/v1/auth/logout")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert data["message"] == "Logout successful"

    async def test_benchmark_logout_success(self, benchmark: BenchmarkFixture, async_client: httpx.AsyncClient) -> None:
        async def logout() -> httpx.Response:
            return await async_client.post("/api/v1/auth/logout")

        response = await benchmark(logout)
        assert response.status_code == status.HTTP_200_OK
