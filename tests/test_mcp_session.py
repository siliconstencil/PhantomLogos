import os
import time

import pytest

from src.architrave.mcp.mcp_session import MCPSession


def test_mcp_session_init():
    session = MCPSession(name="test_srv", command="slm", args=["mcp"], enabled=False)
    assert session.name == "test_srv"
    assert not session.enabled
    assert not session.healthy


def test_mcp_session_disabled():
    session = MCPSession(name="test_srv", command="slm", args=["mcp"], enabled=False)
    with pytest.raises(RuntimeError, match="disabled"):
        session.call_tool_sync("test_tool", {})


def test_mcp_session_shutdown_cleanup():
    import psutil

    # 1. Start session
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    slm_path = os.path.join(project_root, ".venv", "Scripts", "slm.exe") if os.name == "nt" else os.path.join(project_root, ".venv", "bin", "slm")
    session = MCPSession(
        name="test_srv",
        command=slm_path,
        args=["mcp"],
        env={"PYTHONPATH": project_root},
        timeout=30.0,
    )

    active_pids = set()
    try:
        assert session._ensure_connected() is True
        time.sleep(1.0)

        my_pid = os.getpid()

        def get_child_slm_processes():
            procs = []
            for p in psutil.process_iter(["pid", "name", "cmdline", "ppid"]):
                try:
                    cmdline = p.info.get("cmdline")
                    if cmdline and any(
                        "slm" in arg or "superlocalmemory" in arg for arg in cmdline
                    ):
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

        active_procs = get_child_slm_processes()
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
