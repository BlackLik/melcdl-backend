import httpx
from fastapi import status
from pytest_benchmark.fixture import BenchmarkFixture


class TestCommon:
    async def test_health_check(self, async_client: httpx.AsyncClient) -> None:
        response = await async_client.get("/api/health")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"message": "OK"}

    async def test_benchmark_health_check(self, benchmark: BenchmarkFixture, async_client: httpx.AsyncClient) -> None:
        async def health() -> httpx.Response:
            return await async_client.get("/api/health")

        benchmark.group = "health_check"
        response = await benchmark(health)
        assert response.status_code == status.HTTP_200_OK
