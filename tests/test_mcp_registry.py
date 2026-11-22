from src.architrave.mcp.mcp_registry import MCPRegistry, get_mcp_registry


def test_get_mcp_registry_singleton():
    reg1 = get_mcp_registry()
    reg2 = get_mcp_registry()
    assert reg1 is reg2


def test_mcp_registry_load_fallback():
    """A registry without a config file must not invent an SLM stdio session.

    SuperLocalMemory is reached over its own HTTP daemon, so the registry
    never creates an "slm" server.
    """
    registry = MCPRegistry()
    assert "slm" not in registry.get_all_sessions()
    assert "slm" not in registry.config.mcpServers
