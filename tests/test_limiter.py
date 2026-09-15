import pytest
from fastapi import FastAPI, Request
from httpx import AsyncClient, ASGITransport
from fastapi_redis_sliding_limiter import rate_limit, init_limiter

@pytest.fixture
def app():
    fastapi_app = FastAPI()
    init_limiter() # In-memory mode for unit testing

    @fastapi_app.get("/limited")
    @rate_limit(requests=2, window_seconds=10)
    async def limited_route(request: Request):
        return {"status": "ok"}

    return fastapi_app

@pytest.mark.asyncio
async def test_sliding_window_rate_limiting(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Request 1: Allowed
        r1 = await client.get("/limited")
        assert r1.status_code == 200

        # Request 2: Allowed
        r2 = await client.get("/limited")
        assert r2.status_code == 200

        # Request 3: Blocked (Limit = 2)
        r3 = await client.get("/limited")
        assert r3.status_code == 429
        assert "Retry-After" in r3.headers
        assert "Too Many Requests" in r3.json()["detail"]
