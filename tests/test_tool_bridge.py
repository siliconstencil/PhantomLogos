import os

import pytest

from src.clotho.bridge import ToolBridge


# [SRC:axis_10]
@pytest.mark.asyncio
async def test_tool_bridge_ls():
    bridge = ToolBridge("test_ls")
    result = await bridge.execute("ls", [os.getcwd()])
    assert isinstance(result, dict)
    output = result["output"]
    assert isinstance(output, str)
    assert "src" in output or "cognition" in output or "tests" in output


@pytest.mark.asyncio
async def test_tool_bridge_unknown_tool():
    bridge = ToolBridge("test_unknown")
    result = await bridge.execute("nonexistent_tool", {})
    output = result["output"]
    assert isinstance(output, str)
    assert "Unknown" in output


@pytest.mark.asyncio
async def test_tool_bridge_logs_events():
    bridge = ToolBridge("test_logging")
    await bridge.execute("ls", [os.getcwd()])
    history = bridge.log.get_history(limit=5)
    request_found = any(
        e["type"] == "tool.request" and e.get("payload", {}).get("tool") == "ls" for e in history
    )
    response_found = any(
        e["type"] == "tool.response" and e.get("payload", {}).get("tool") == "ls" for e in history
    )
    assert request_found
    assert response_found


@pytest.mark.asyncio
async def test_tool_bridge_mapper():
    bridge = ToolBridge("test_mapper")
    result = await bridge.execute("mapper", {"action": "suggest", "keywords": ["auth", "login"]})
    assert isinstance(result, dict)
    assert "output" in result


@pytest.mark.asyncio
async def test_tool_bridge_skill_list():
    bridge = ToolBridge("test_skill")
    result = await bridge.execute("skill", "list")
    output = result["output"]
    assert isinstance(output, str)
    assert len(output) > 5  # Should contain at least one skill dict string


@pytest.mark.asyncio
async def test_tool_bridge_shell_rejection():
    """Verify that 'shell' tool is rejected for security (H2)."""
    bridge = ToolBridge("test_rejection")
    result = await bridge.execute("shell", "echo hello")
    output = str(result.get("output", ""))
    assert "Unknown" in output or "security" in output.lower() or "rejected" in output.lower()
