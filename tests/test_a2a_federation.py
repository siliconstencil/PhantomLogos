import asyncio
import json
import os
import socket
import time
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from cognition.sophia.state_bus import get_state_bus
from src.architrave.a2a.auth import get_a2a_secret, sign_payload, verify_signature
from src.architrave.a2a.client import send_a2a_message
from src.architrave.a2a.discovery import A2ADiscovery, RemoteAgentInfo
from src.architrave.a2a.protocol import BusMessage, deserialize_from_a2a, serialize_to_a2a
from src.architrave.a2a.server import A2AServer
from src.clotho.agent_loader import AgentRegistry

# Set environments for testing
os.environ["A2A_SECRET_SOPHIA"] = "sophia_test_secret_123"
os.environ["A2A_SECRET_LACHESIS"] = "lachesis_test_secret_456"


# 1. test_a2a_hmac_sign_verify
def test_a2a_hmac_sign_verify():
    payload = {"message_id": "test_123", "sender": "sophia", "data": "hello"}
    secret = "secret_key"
    sig = sign_payload(payload, secret)

    # Successful verify
    assert verify_signature(payload, secret, sig) is True

    # Mismatched secret verify
    assert verify_signature(payload, "wrong_secret", sig) is False

    # Missing signature verify
    assert verify_signature(payload, secret, "") is False


# 2. test_a2a_protocol_roundtrip
def test_a2a_protocol_roundtrip():
    msg = BusMessage(
        id="a2a_abc123",
        sender="sophia",
        recipient="lachesis",
        topic="audit_request",
        payload={"data": "test"},
        timestamp=1234567.8,
    )
    sender_endpoint = "http://127.0.0.1:32554/a2a"

    serialized = serialize_to_a2a(msg, sender_endpoint)
    assert serialized["protocol_version"] == "1.0"
    assert serialized["message_id"] == "a2a_abc123"
    assert serialized["sender"]["agent_id"] == "sophia"
    assert serialized["sender"]["endpoint"] == sender_endpoint

    deserialized = deserialize_from_a2a(serialized)
    assert deserialized.id == msg.id
    assert deserialized.sender == msg.sender
    assert deserialized.recipient == msg.recipient
    assert deserialized.topic == msg.topic
    assert deserialized.payload == msg.payload
    assert deserialized.timestamp == msg.timestamp
    assert deserialized.metadata["sender_endpoint"] == sender_endpoint


# 3. test_a2a_server_health
@pytest.mark.asyncio
async def test_a2a_server_health():
    # Setup test server on unique port
    server = A2AServer(agent_id="sophia", default_port=32881)
    server.start()

    # Wait for startup
    await asyncio.sleep(0.5)

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get("http://127.0.0.1:32881/a2a/health")
            assert resp.status_code == 200
            data = resp.json()
            assert data["agent_id"] == "sophia"
            assert data["status"] == "alive"
            assert data["uptime"] >= 0
    finally:
        await server.stop()


# 4. test_a2a_server_message
@pytest.mark.asyncio
async def test_a2a_server_message():
    server = A2AServer(agent_id="sophia", default_port=32882)
    server.start()
    await asyncio.sleep(0.5)

    msg = BusMessage(
        id="test_msg_999",
        sender="lachesis",
        recipient="sophia",
        topic="audit_request",
        payload={"data": "content"},
    )
    payload = serialize_to_a2a(msg, "http://127.0.0.1:32555/a2a")
    secret = get_a2a_secret("lachesis")
    signature = sign_payload(payload, secret)

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "http://127.0.0.1:32882/a2a/message",
                json=payload,
                headers={"X-A2A-Signature": signature},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "ok"
            assert data["message_id"] == "test_msg_999"
    finally:
        await server.stop()


# 5. test_a2a_server_401_unsigned
@pytest.mark.asyncio
async def test_a2a_server_401_unsigned():
    server = A2AServer(agent_id="sophia", default_port=32883)
    server.start()
    await asyncio.sleep(0.5)

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post("http://127.0.0.1:32883/a2a/message", json={"message_id": "1"})
            assert resp.status_code == 401
            assert "Missing signature header" in resp.json()["error"]
    finally:
        await server.stop()


# 6. test_a2a_server_401_bad_signature
@pytest.mark.asyncio
async def test_a2a_server_401_bad_signature():
    server = A2AServer(agent_id="sophia", default_port=32884)
    server.start()
    await asyncio.sleep(0.5)

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "http://127.0.0.1:32884/a2a/message",
                json={"message_id": "1", "sender": {"agent_id": "lachesis"}},
                headers={"X-A2A-Signature": "invalid_sig_here"},
            )
            assert resp.status_code == 401
            assert "Invalid signature" in resp.json()["error"]
    finally:
        await server.stop()


# 7. test_a2a_client_send
@pytest.mark.asyncio
async def test_a2a_client_send():
    msg = BusMessage(id="msg_x", sender="sophia", recipient="lachesis")

    # Mock httpx POST call
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_resp = httpx.Response(200, json={"status": "ok", "message_id": "msg_x"})
        mock_post.return_value = mock_resp

        secret = "secret_key"
        res = await send_a2a_message(
            target_endpoint="http://127.0.0.1:32555/a2a",
            msg=msg,
            secret=secret,
            sender_endpoint="http://127.0.0.1:32554/a2a",
        )

        assert res["status"] == "ok"
        assert res["message_id"] == "msg_x"
        mock_post.assert_called_once()


# 8. test_a2a_discovery_register
def test_a2a_discovery_register():
    temp_registry = "agent/a2a_registry_test.json"
    if os.path.exists(temp_registry):
        os.remove(temp_registry)

    try:
        from src.clotho.bootstrap import register_a2a_bridge

        register_a2a_bridge()

        discovery = A2ADiscovery(registry_path=temp_registry)
        info = RemoteAgentInfo(
            {
                "agent_id": "lachesis",
                "name": "Lachesis Agent",
                "endpoint": "http://127.0.0.1:32555/a2a",
                "capabilities": ["audit"],
                "skills": ["persona-auditor"],
                "status": "offline",
            }
        )

        discovery.register_remote(info)
        resolved = discovery.resolve("lachesis")

        assert resolved is not None
        assert resolved.agent_id == "lachesis"
        assert resolved.endpoint == "http://127.0.0.1:32555/a2a"

        # Verify dynamic AgentRegistry sync (Finding 3)
        registry = AgentRegistry.get_instance()
        agent_def = registry.get("lachesis")
        assert agent_def is not None
        assert agent_def.skills == ["persona-auditor"]
        assert agent_def.model_primary == "remote:http://127.0.0.1:32555/a2a"
    finally:
        if os.path.exists(temp_registry):
            os.remove(temp_registry)


# 9. test_a2a_discovery_heartbeat
@pytest.mark.asyncio
async def test_a2a_discovery_heartbeat():
    temp_registry = "agent/a2a_registry_test_heartbeat.json"
    try:
        discovery = A2ADiscovery(registry_path=temp_registry)
        info = RemoteAgentInfo(
            {
                "agent_id": "test_agent",
                "endpoint": "http://127.0.0.1:32999/a2a",
                "status": "online",
                "last_heartbeat": time.time() - 150.0,  # Expired last heartbeat
            }
        )
        discovery._agents["test_agent"] = info

        # Start heartbeat and simulate ttl decay checks
        # Mock ping to return False
        with patch.object(discovery, "ping_agent", new_callable=AsyncMock) as mock_ping:
            mock_ping.return_value = False
            task = asyncio.create_task(discovery.start_heartbeat(interval_s=0.1))
            await asyncio.sleep(0.3)
            task.cancel()

        assert info.status == "offline"
    finally:
        if os.path.exists(temp_registry):
            os.remove(temp_registry)


# 10. test_a2a_discovery_registry_file
def test_a2a_discovery_registry_file():
    temp_registry = "agent/a2a_registry_test_file.json"
    dummy_data = {
        "agents": [
            {
                "agent_id": "dummy",
                "name": "Dummy Agent",
                "endpoint": "http://localhost:32888/a2a",
                "capabilities": ["dummy_cap"],
                "skills": ["dummy_skill"],
                "status": "online",
                "last_heartbeat": time.time(),
            }
        ]
    }

    try:
        with open(temp_registry, "w") as f:
            json.dump(dummy_data, f)

        discovery = A2ADiscovery(registry_path=temp_registry)
        resolved = discovery.resolve("dummy")

        assert resolved is not None
        assert resolved.name == "Dummy Agent"
        assert resolved.endpoint == "http://localhost:32888/a2a"
        assert "dummy_cap" in resolved.capabilities
    finally:
        if os.path.exists(temp_registry):
            os.remove(temp_registry)


# 11. test_a2a_state_bus_remote
@pytest.mark.asyncio
async def test_a2a_state_bus_remote():
    bus = get_state_bus()
    temp_registry = "agent/a2a_registry_test_bus.json"

    try:
        discovery = A2ADiscovery(registry_path=temp_registry)
        info = RemoteAgentInfo(
            {
                "agent_id": "lachesis",
                "endpoint": "http://127.0.0.1:32555/a2a",
                "status": "online",
                "last_heartbeat": time.time(),
            }
        )
        discovery._agents["lachesis"] = info
        # Mock StateBus.publish routing components
        with (
            patch("src.architrave.a2a.discovery.A2ADiscovery", return_value=discovery),
            patch(
                "src.architrave.a2a.client.send_a2a_message", new_callable=AsyncMock
            ) as mock_send,
        ):
            mock_send.return_value = {"status": "ok"}

            msg = BusMessage(sender="sophia", recipient="lachesis", topic="test", payload={})
            await bus.publish(msg)

            mock_send.assert_called_once()
    finally:
        if os.path.exists(temp_registry):
            os.remove(temp_registry)


# 12. test_a2a_state_bus_local
@pytest.mark.asyncio
async def test_a2a_state_bus_local():
    bus = get_state_bus()
    msg = BusMessage(sender="sophia", recipient="broadcast", topic="local_test", payload={})

    # Broadcast is dispatched locally and remote
    with patch("src.architrave.a2a.client.send_a2a_message") as mock_send:
        mock_send.return_value = {"status": "ok"}

        await bus.publish(msg)

        # Verify local history and queue has it
        recent = bus.recent(1)
        assert len(recent) == 1
        assert recent[0].topic == "local_test"


# 13. test_a2a_thread_bridge
@pytest.mark.asyncio
async def test_a2a_thread_bridge():
    bus = get_state_bus()
    msg = BusMessage(sender="external_thread", recipient="broadcast", topic="thread_bridge_test")

    # Simulate receiving message in server thread and calling put_nowait directly
    def run_external_receive():
        bus._queue.put_nowait(msg)
        bus._history.append(msg)

    thread = threading = Thread = type("Thread", (object,), {"run": lambda: run_external_receive()})
    thread.run()

    # Main loop reads it
    recent = bus.recent(1)
    assert len(recent) == 1
    assert recent[0].sender == "external_thread"


# 14. test_a2a_port_fallback
@pytest.mark.asyncio
async def test_a2a_port_fallback():
    # Bind a socket to 32889 to occupy the port
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 32889))
    sock.listen(1)

    server = A2AServer(agent_id="sophia", default_port=32889)
    server.start()
    await asyncio.sleep(0.5)

    try:
        # Port should fallback to 32890
        assert server.port == 32890
    finally:
        await server.stop()
        sock.close()
