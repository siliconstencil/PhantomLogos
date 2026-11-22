import os
import sys
import time

import pytest

from src.architrave.mcp.mcp_session import MCPSession

_TEST_SERVER_SOURCE = """
from mcp.server.fastmcp import FastMCP

server = FastMCP("phantom-test")


@server.tool()
def ping() -> str:
    return "pong"


if __name__ == "__main__":
    server.run()
"""


def test_mcp_session_init():
    session = MCPSession(name="test_srv", command="server-binary", args=[], enabled=False)
    assert session.name == "test_srv"
    assert not session.enabled
    assert not session.healthy


def test_mcp_session_disabled():
    session = MCPSession(name="test_srv", command="server-binary", args=[], enabled=False)
    with pytest.raises(RuntimeError, match="disabled"):
        session.call_tool_sync("test_tool", {})


def test_mcp_session_shutdown_cleanup():
    """A spawned MCP server process must be gone after the session is shut down."""
    import psutil

    from src.utils.project_path import get_data_dir

    server_path = get_data_dir() / "phantom_test_mcp_server.py"
    server_path.write_text(_TEST_SERVER_SOURCE, encoding="utf-8")

    session = MCPSession(
        name="test_srv",
        command=sys.executable,
        args=[str(server_path)],
        env={"PYTHONPATH": os.getcwd()},
        timeout=30.0,
    )

    active_pids = set()
    try:
        assert session._ensure_connected() is True
        time.sleep(1.0)

        my_pid = os.getpid()

        def get_child_server_processes():
            procs = []
            for p in psutil.process_iter(["pid", "name", "cmdline", "ppid"]):
                try:
                    cmdline = p.info.get("cmdline")
                    if cmdline and any(server_path.name in arg for arg in cmdline):
                        if p.info["ppid"] == my_pid:
                            procs.append(p)
                        else:
                            try:
                                parent = psutil.Process(p.info["ppid"])
                                if parent.ppid() == my_pid:
                                    procs.append(p)
                            except Exception:
                                pass
                except Exception:
                    pass
            return procs

        active_procs = get_child_server_processes()
        assert len(active_procs) > 0, "No child processes spawned by MCPSession"
        active_pids = {p.pid for p in active_procs}
        print(f"Spawned PIDs under test: {active_pids}")

    finally:
        # 2. Call shutdown
        session.shutdown()

    # Wait a moment for OS/process tree cleanup to complete
    time.sleep(2.0)

    # 3. Verify they are all terminated
    for pid in active_pids:
        assert not psutil.pid_exists(pid), f"Process {pid} still exists after shutdown (zombie)!"
    print("All processes cleaned up successfully! No zombie processes found.")
