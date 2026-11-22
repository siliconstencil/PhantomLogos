"""Tests for the HTTP-only SuperLocalMemory transport.

The SLM daemon is reached over HTTP on port 8765. It is not an MCP stdio
server any more, so the registry must never create an "slm" session and the
bootstrap must start the daemon as its own process.
"""

import http.server
import json
import os
import threading
from typing import Any

import pytest

from src.architrave.mcp.mcp_registry import MCPRegistry
from src.clotho.hermes_mcp import discover_slm_port, start_slm, start_slm_server
from src.utils.slm_status import check_slm


class _HealthHandler(http.server.BaseHTTPRequestHandler):
    payload: dict[str, Any] = {"status": "ok"}

    def do_GET(self) -> None:
        body = json.dumps(type(self).payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args: Any) -> None:
        return


@pytest.fixture
def fake_slm_daemon():
    servers: list[http.server.ThreadingHTTPServer] = []

    def _start(payload: dict[str, Any]) -> int:
        handler = type("Handler", (_HealthHandler,), {"payload": payload})
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        servers.append(server)
        return int(server.server_address[1])

    yield _start

    for server in servers:
        server.shutdown()
        server.server_close()


def test_discover_slm_port_finds_healthy_daemon(fake_slm_daemon):
    port = fake_slm_daemon({"status": "ok", "version": "4.2.34"})
    assert discover_slm_port("127.0.0.1", port) == "ours"


def test_discover_slm_port_rejects_foreign_service(fake_slm_daemon):
    port = fake_slm_daemon({"status": "degraded", "service": "something-else"})
    assert discover_slm_port("127.0.0.1", port) == "foreign"


def test_discover_slm_port_reports_free_port():
    assert discover_slm_port("127.0.0.1", 18765) == "none"


def test_registry_does_not_create_an_slm_session(tmp_path):
    config_path = tmp_path / "mcp_config.json"
    config_path.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "slm": {
                        "command": "slm",
                        "args": ["mcp"],
                        "env": {},
                        "timeout": 30,
                        "enabled": True,
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    registry = MCPRegistry(config_path=str(config_path))

    assert "slm" not in registry.get_all_sessions()
    assert "slm" not in registry.config.mcpServers


def test_start_slm_server_launches_the_daemon_as_a_process(monkeypatch, tmp_path):
    launched: list[list[str]] = []

    class _FakePopen:
        def __init__(self, cmd, **kwargs):
            launched.append(list(cmd))
            self.kwargs = kwargs

    monkeypatch.setattr("src.clotho.hermes_mcp.discover_slm_port", lambda *a, **k: "none")
    monkeypatch.setenv("SLM_BIN", str(tmp_path / "slm"))
    monkeypatch.setattr("subprocess.Popen", _FakePopen)

    start_slm_server()

    assert launched == [[str(tmp_path / "slm"), "serve", "start"]]


def test_start_slm_server_without_slm_bin_does_nothing(monkeypatch):
    monkeypatch.setattr("src.clotho.hermes_mcp.discover_slm_port", lambda *a, **k: "none")
    monkeypatch.delenv("SLM_BIN", raising=False)
    monkeypatch.setattr(
        "subprocess.Popen",
        lambda *args, **kwargs: pytest.fail("no daemon may be started without SLM_BIN"),
    )

    start_slm_server()


def test_start_slm_does_not_open_an_mcp_session(monkeypatch):
    monkeypatch.setenv("SLM_ENABLED", "true")

    def _fail(*args: Any, **kwargs: Any) -> None:
        pytest.fail("the MCP registry must not be used for SLM any more")

    monkeypatch.setattr("src.architrave.mcp.mcp_registry.get_mcp_registry", _fail)

    start_slm()


def test_check_slm_reports_disabled_as_info(monkeypatch):
    monkeypatch.setenv("SLM_ENABLED", "false")
    status, detail = check_slm()
    assert status == "INFO"
    assert "disabled" in detail.lower()


def test_check_slm_reports_a_healthy_daemon(monkeypatch, fake_slm_daemon):
    port = fake_slm_daemon({"status": "ok"})
    monkeypatch.setenv("SLM_ENABLED", "true")
    monkeypatch.setenv("SLM_HTTP_PORT", str(port))

    status, detail = check_slm()

    assert status == "OK"
    assert str(port) in detail


def test_check_slm_reports_a_missing_daemon_as_info(monkeypatch):
    monkeypatch.setenv("SLM_ENABLED", "true")
    monkeypatch.setenv("SLM_HTTP_PORT", "18765")

    status, _detail = check_slm()

    assert status == "INFO"


def test_bootstrap_knows_the_with_slm_flag():
    from scripts.bootstrap import parse_args

    args = parse_args(["--with-slm"])
    assert args.with_slm is True
    assert parse_args([]).with_slm is False


def test_bootstrap_installs_slm_into_a_separate_venv(monkeypatch, tmp_path):
    from scripts import bootstrap

    commands: list[list[str]] = []

    def _fake_run(cmd, **kwargs):
        commands.append(list(cmd))
        return None

    monkeypatch.setattr(bootstrap.subprocess, "run", _fake_run)
    monkeypatch.chdir(tmp_path)

    bootstrap.install_slm_venv()

    assert any(".venv-slm" in part for cmd in commands for part in cmd)
    assert any("superlocalmemory" in part for cmd in commands for part in cmd)
    assert all(
        ".venv-slm" not in cmd[0] or cmd[0].endswith(("python", "python3", "python3.12"))
        for cmd in commands
    )


def test_env_example_only_lists_known_variables():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_example = os.path.join(root, ".env.example")
    if not os.path.exists(env_example):
        pytest.skip(".env.example is not published yet")

    with open(env_example, encoding="utf-8") as handle:
        lines = handle.read().splitlines()

    names = [
        line.split("=", 1)[0].strip()
        for line in lines
        if line.strip() and not line.strip().startswith("#") and "=" in line
    ]
    assert names, ".env.example must list at least one variable"

    sources: list[str] = []
    for folder in ("src", "cognition", "scripts"):
        for dirpath, _dirnames, filenames in os.walk(os.path.join(root, folder)):
            sources.extend(
                os.path.join(dirpath, filename)
                for filename in filenames
                if filename.endswith(".py")
            )

    chunks: list[str] = []
    for path in sources:
        with open(path, encoding="utf-8") as handle:
            chunks.append(handle.read())
    corpus = "\n".join(chunks)

    unknown = [name for name in names if name not in corpus]
    assert not unknown, f"unknown variables in .env.example: {unknown}"
