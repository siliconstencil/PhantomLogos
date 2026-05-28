from unittest.mock import MagicMock, patch

from src.architrave.mcp.mcp_tool_bridge import discover_and_register_mcp_tools


class MockToolBridge:
    _mcp_handlers = {}

    @classmethod
    def register_mcp_tool(cls, server_name: str, tool_name: str, handler):
        cls._mcp_handlers[f"{server_name}_{tool_name}"] = handler


def test_discover_and_register_mcp_tools():
    MockToolBridge._mcp_handlers = {}

    mock_session = MagicMock()
    # Mocking list_tools_sync to return a list of Mock tools
    mock_tool = MagicMock()
    mock_tool.name = "test_tool"
    mock_session.list_tools_sync.return_value = [mock_tool]
    mock_session.enabled = True

    mock_registry = MagicMock()
    mock_registry.get_all_sessions.return_value = {"mock_srv": mock_session}

    with patch("src.architrave.mcp.mcp_tool_bridge.get_mcp_registry", return_value=mock_registry):
        discover_and_register_mcp_tools(MockToolBridge)

    assert "mock_srv_test_tool" in MockToolBridge._mcp_handlers
