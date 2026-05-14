import json
import os
import subprocess
import sys

import pytest


# [SRC:axis_12]
def run_hermes(cmd_args):
    """Helper to run hermes_cli.py via subprocess."""
    cli_path = os.path.join("scripts", "hermes_cli.py")
    if not os.path.exists(cli_path):
        pytest.skip("hermes_cli.py not found at scripts/hermes_cli.py")
    full_cmd = [sys.executable, cli_path] + cmd_args
    result = subprocess.run(full_cmd, capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 0, f"Hermes CLI failed: {result.stderr}"
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return result.stdout


@pytest.mark.asyncio
async def test_hermes_full_lifecycle():
    """Verifies init -> save -> load -> close cycle via Hermes CLI."""
    # 1. Init
    init_res = run_hermes(["init"])
    assert "session_id" in init_res
    session_id = init_res["session_id"]
    assert session_id.startswith("hermes_")

    # 2. Save Fact
    save_fact_res = run_hermes(
        [
            "save",
            "--session",
            session_id,
            "--type",
            "fact",
            "--subject",
            "audit_test",
            "--object",
            "passed_v11.3",
        ]
    )
    assert save_fact_res["status"] == "saved"

    # 3. Save Event
    save_event_res = run_hermes(
        [
            "save",
            "--session",
            session_id,
            "--type",
            "event",
            "--data",
            json.dumps({"action": "test_verification", "detail": "Stability check phase"}),
        ]
    )
    assert save_event_res["status"] == "saved"

    # 4. Load
    load_res = run_hermes(["load", "--session", session_id])
    assert load_res["session_id"] == session_id
    assert "facts" in load_res
    fact_found = any(f["subject"] == "audit_test" for f in load_res["facts"])
    assert fact_found, "Saved fact not found in load output"

    # 5. Close
    close_res = run_hermes(["close", "--session", session_id])
    assert close_res["status"] == "closed"
