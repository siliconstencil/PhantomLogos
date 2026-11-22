import sys
from unittest.mock import patch

import pytest

from src.muscle.local_runtime import LocalRuntime


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX pkill path")
def test_stop_active_does_not_target_ollama_llama_server():
    with patch("src.muscle.local_runtime.subprocess.run") as run:
        LocalRuntime.stop_active()

    cmd = run.call_args[0][0]
    assert cmd[0] == "pkill"
    assert "llama-server" not in cmd[2]
    assert cmd[2] == "llama-(cli|mtmd-cli|llava-cli)"
