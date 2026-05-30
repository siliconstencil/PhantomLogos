from unittest.mock import MagicMock

import pytest

from src.architrave.a2a.bridge import FederationBridge


def test_federation_bridge_constructor():
    bridge = FederationBridge(agent_id="test_agent", local_endpoint="http://localhost:0")
    assert bridge.agent_id == "test_agent"
    assert bridge.local_endpoint == "http://localhost:0"


@pytest.mark.asyncio
async def test_federation_bridge_unknown_agent():
    bridge = FederationBridge(agent_id="test_agent", local_endpoint="http://localhost:0")
    result = await bridge.send_to_agent("nonexistent_agent", "test", {})
    assert result["status"] == "error"
    assert "Unknown agent" in result["error"]


@pytest.mark.asyncio
async def test_federation_bridge_broadcast_no_agents():
    mock_discovery = MagicMock()
    mock_discovery.list_online_agents.return_value = []
    bridge = FederationBridge(
        agent_id="test_agent", local_endpoint="http://localhost:0", discovery=mock_discovery
    )
    results = await bridge.broadcast("test", {})
    assert results == []


def test_federation_bridge_get_local_secret():
    bridge = FederationBridge(agent_id="test_agent", local_endpoint="http://localhost:0")
    secret = bridge._get_local_secret()
    assert isinstance(secret, str)
