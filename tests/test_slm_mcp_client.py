from unittest.mock import MagicMock, patch

from cognition.mnemosyne.semantic_store import SemanticStore
from src.architrave.mcp import SLMClient, get_slm_client
from src.atropos.matryoshka_service import MatryoshkaService


def test_slm_config_and_singleton():
    client = get_slm_client()
    assert isinstance(client, SLMClient)
    # Default fallback endpoint
    assert "http://localhost:8081" in client.config.endpoint
    assert client.config.mcp_cmd == "slm mcp"


def test_slm_active_flag_decoupled(monkeypatch):
    monkeypatch.setenv("SLM_ENABLED", "false")
    store = SemanticStore()
    assert not store._is_slm_active()

    # Mock SLM client to return True for health check
    mock_slm = MagicMock()
    mock_slm.health.return_value = True

    with monkeypatch.context() as m:
        m.setenv("SLM_ENABLED", "true")
        with patch("src.architrave.mcp.get_slm_client", return_value=mock_slm):
            assert store._is_slm_active()


def test_matryoshka_service_active_flag_decoupled(monkeypatch):
    monkeypatch.setenv("SLM_ENABLED", "false")
    svc = MatryoshkaService()
    assert not svc._is_slm_active()

    # Mock SLM client to return True for health check
    mock_slm = MagicMock()
    mock_slm.health.return_value = True

    with monkeypatch.context() as m:
        m.setenv("SLM_ENABLED", "true")
        with patch("src.architrave.mcp.get_slm_client", return_value=mock_slm):
            assert svc._is_slm_active()
