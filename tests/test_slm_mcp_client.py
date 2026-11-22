from unittest.mock import MagicMock, patch

from cognition.mnemosyne.semantic_store import SemanticStore
from src.architrave.mcp import SLMClient, SLMConfig, get_slm_client
from src.atropos.matryoshka_service import MatryoshkaService


def test_slm_config_and_singleton():
    client = get_slm_client()
    assert isinstance(client, SLMClient)
    # The daemon speaks HTTP on port 8765; the MCP stdio command is gone.
    assert client.config.http_port == 8765
    assert client.config.http_op_timeout > 0
    assert get_slm_client() is client


def test_slm_config_reads_the_port_from_the_environment(monkeypatch):
    monkeypatch.setenv("SLM_HTTP_PORT", "9911")
    assert SLMConfig.from_env().http_port == 9911


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
