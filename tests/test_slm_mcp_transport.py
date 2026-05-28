import json
from unittest.mock import MagicMock, patch

from src.architrave.mcp import SLMClient, SLMConfig


def test_config_mapping():
    cfg = SLMConfig(mcp_cmd="custom cmd", mcp_timeout=45)
    client = SLMClient(config=cfg)
    assert client.config.mcp_cmd == "custom cmd"
    assert client.config.mcp_timeout == 45


def test_remember_mapping():
    client = SLMClient()
    mock_session = MagicMock()

    with patch.object(client, "_get_session", return_value=mock_session):
        entry = {
            "text": "test memory text",
            "error_type": "linter_error",
            "importance": 0.8,
            "metadata": {"category": "syntax", "tags": ["python", "mcp"]},
        }
        res = client.remember(entry, table_name="semantic_memory")
        assert res is True

        mock_session.call_tool_sync.assert_called_once()
        name, params = mock_session.call_tool_sync.call_args[0]
        assert name == "remember"
        assert params["content"] == "test memory text"
        assert "linter_error" in params["tags"]
        assert "meta:category:syntax" in params["tags"]
        assert any("python" in t for t in params["tags"])
        assert params["importance"] == 0.8
        assert params["project"] == "semantic_memory"


def test_search_mapping():
    client = SLMClient()
    mock_session = MagicMock()
    mock_session.call_tool_sync.return_value = {
        "results": [{"text": "matching text", "score": 0.95}]
    }

    with patch.object(client, "_get_session", return_value=mock_session):
        res = client.search(
            query="search query", limit=3, table_name="failure_memory", session_id="test-session"
        )
        assert len(res) == 1
        assert res[0]["text"] == "matching text"

        mock_session.call_tool_sync.assert_called_once()
        name, params = mock_session.call_tool_sync.call_args[0]
        assert name == "recall"
        assert params["query"] == "search query"
        assert params["limit"] == 3
        assert params["project"] == "failure_memory"
        assert params["session_id"] == "test-session"


def test_tag_serialization_and_axis_id():
    import numpy as np

    client = SLMClient()
    mock_session = MagicMock()

    with patch.object(client, "_get_session", return_value=mock_session):
        entry = {
            "text": "axis memory",
            "vector": np.zeros(256),
            "metadata": {"category": "test"},
            "timestamp": 1234567.0,
        }
        res = client.remember(entry, table_name="test_table", agent_id="agent-007", axis_id=14)
        assert res is True

        mock_session.call_tool_sync.assert_called_once()
        name, params = mock_session.call_tool_sync.call_args[0]
        assert name == "remember"
        tags = params["tags"]

        # Verify prefixes exist
        assert any(t.startswith("v:") for t in tags)
        assert any(t.startswith("meta:") for t in tags)
        assert "t:1234567.0" in tags
        assert "a:agent-007" in tags
        assert "x:14" in tags


def test_search_session_id_filter():
    client = SLMClient()
    mock_session = MagicMock()

    from src.architrave.mcp.slm_client import _serialize_meta

    meta_encoded = _serialize_meta({"dummy": "value"})

    # Mocking recall output with three records:
    # 1. Matching requested session_id
    # 2. Matching "system" session_id
    # 3. Mismatching session_id
    mock_session.call_tool_sync.return_value = {
        "results": [
            {"content": "match 1", "tags": [f"m:{meta_encoded}"], "session_id": "my-session"},
            {"content": "match 2", "tags": [f"m:{meta_encoded}"], "session_id": "system"},
            {"content": "mismatch", "tags": [f"m:{meta_encoded}"], "session_id": "other-session"},
        ]
    }

    with patch.object(client, "_get_session", return_value=mock_session):
        res = client.search(query="query", limit=5, table_name="test", session_id="my-session")
        # Should filter out "mismatch", leaving "match 1" and "match 2"
        assert len(res) == 2
        contents = [r["text"] for r in res]
        assert "match 1" in contents
        assert "match 2" in contents
        assert "mismatch" not in contents


def test_normalize_result_slm_format():
    import numpy as np

    from src.architrave.mcp.slm_client import _normalize_result, _serialize_meta, _serialize_vector

    vec = np.ones(256)
    meta = {"key": "val"}

    raw = {
        "content": "test rule content",
        "tags": [
            f"v:{_serialize_vector(vec)}",
            f"m:{_serialize_meta(meta)}",
            "t:987654.0",
            "a:agent-47",
            "x:12",
        ],
        "session_id": "my-session",
        "importance": 0.9,
    }

    norm = _normalize_result(raw)
    assert norm["text"] == "test rule content"
    assert norm["prevention_rule"] == "test rule content"
    assert len(norm["vector"]) == 256
    assert "key" in json.loads(norm["metadata"])
    assert norm["timestamp"] == 987654.0
    assert norm["agent_id"] == "agent-47"
    assert norm["axis_id"] == 12
    assert norm["session_id"] == "my-session"


def test_observe_mapping():
    client = SLMClient()
    mock_session = MagicMock()

    with patch.object(client, "_get_session", return_value=mock_session):
        client.observe("test observe text", agent_id="observe-agent")
        mock_session.call_tool_sync.assert_called_once_with(
            "observe", {"content": "test observe text", "agent_id": "observe-agent"}
        )

    mock_session.reset_mock()

    # Test async
    async def run_async_test():
        with patch.object(client, "_get_session", return_value=mock_session):
            await client.aobserve("async test", agent_id="async-agent")
            mock_session.call_tool_async.assert_called_once_with(
                "observe", {"content": "async test", "agent_id": "async-agent"}
            )

    import asyncio

    asyncio.run(run_async_test())
