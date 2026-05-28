from src.architrave.mcp.mcp_registry import MCPRegistry, get_mcp_registry


def test_get_mcp_registry_singleton():
    reg1 = get_mcp_registry()
    reg2 = get_mcp_registry()
    assert reg1 is reg2


def test_mcp_registry_load_fallback():
    registry = MCPRegistry()
    assert "slm" in registry.get_all_sessions()
