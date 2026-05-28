import os
from unittest.mock import MagicMock, patch

import pytest

import cognition.morpheus.monitor as monitor
from cognition.morpheus.monitor import (
    get_cached_gpu_info,
    get_gpu_memory_info,
    set_cached_gpu_info,
)


@pytest.fixture(autouse=True)
def reset_monitor_state():
    # Reset monitor module level variables before each test
    monitor._cached_gpu_info = {}
    monitor._cached_gpu_time = 0.0
    monitor._last_failure_time = 0.0
    if "DISABLE_NVIDIA_SMI" in os.environ:
        del os.environ["DISABLE_NVIDIA_SMI"]
    if "MOCK_GPU" in os.environ:
        del os.environ["MOCK_GPU"]


def test_gpu_monitor_success():
    mock_stdout = "8192, 1024, 7168, 15\n"
    with patch("subprocess.run") as mock_run:
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = mock_stdout
        mock_run.return_value = mock_proc

        info = get_gpu_memory_info()
        assert info["total_gb"] == 8.0
        assert info["used_gb"] == 1.0
        assert info["free_gb"] == 7.0
        assert info["utilization_pct"] == 15.0

        # Check cache is set
        cached = get_cached_gpu_info()
        assert cached is not None
        assert cached["total_gb"] == 8.0


def test_gpu_monitor_disable_env():
    # Set cache first
    set_cached_gpu_info(
        {"total_gb": 16.0, "used_gb": 4.0, "free_gb": 12.0, "utilization_pct": 20.0}
    )

    os.environ["DISABLE_NVIDIA_SMI"] = "true"
    with patch("subprocess.run") as mock_run:
        info = get_gpu_memory_info()
        mock_run.assert_not_called()
        assert info["total_gb"] == 16.0  # returned from cache


def test_gpu_monitor_failure_cooldown():
    # 1. Set cache first
    set_cached_gpu_info({"total_gb": 12.0, "used_gb": 2.0, "free_gb": 10.0, "utilization_pct": 5.0})

    # 2. Mock subprocess.run to raise exception (failure)
    with patch("subprocess.run", side_effect=Exception("nvidia-smi failed")) as mock_run:
        # First call fails, returns cached, sets last_failure_time
        info = get_gpu_memory_info()
        assert info["total_gb"] == 12.0
        assert monitor._last_failure_time > 0.0

    # 3. Subsequent call should hit cooldown and not even call subprocess.run
    with patch("subprocess.run") as mock_run_cooldown:
        info = get_gpu_memory_info()
        mock_run_cooldown.assert_not_called()
        assert info["total_gb"] == 12.0
