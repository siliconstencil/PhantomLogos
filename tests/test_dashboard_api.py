import pytest
from aiohttp.test_utils import TestClient, TestServer

from src.dashboard.api_server import make_app


@pytest.mark.asyncio
async def test_dashboard_endpoints():
    """Verify that all main dashboard endpoints (index, metrics, logs) are responsive and returning correct structures."""
    app = await make_app()
    server = TestServer(app)
    async with TestClient(server) as client:
        # 1. Test index page serving
        resp = await client.get("/")
        assert resp.status == 200
        text = await resp.text()
        assert "Phantom Logos" in text
        assert "Operator Dashboard" in text

        # 2. Test metrics API endpoint
        resp = await client.get("/api/metrics")
        assert resp.status == 200
        data = await resp.json()
        assert "status" in data
        assert data["status"] == "online"
        assert "reliability" in data
        assert "vram" in data
        assert "axes" in data
        assert isinstance(data["axes"], list)

        # 3. Test logs API endpoint
        resp = await client.get("/api/logs")
        assert resp.status == 200
        data = await resp.json()
        assert "logs" in data
        assert isinstance(data["logs"], list)
