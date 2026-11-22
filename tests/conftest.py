import atexit
import os
import shutil
import sys
import tempfile

import pytest

# [SRC:axis_10]
# Ensure project root is in path for all tests to resolve imports without path_insert
sys.path.append(os.getcwd())

# [SRC:axis_10]
# Ensure project root is in path for all tests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# [SRC:axis_10]
# Tests must never write into the real data/ directory. The override is set at
# import time because several stores resolve their database path while the test
# modules are collected.
_TEST_DATA_DIR = tempfile.mkdtemp(prefix="phantom-test-data-")
os.environ["PHANTOM_DATA_DIR"] = _TEST_DATA_DIR
atexit.register(shutil.rmtree, _TEST_DATA_DIR, True)


@pytest.fixture(autouse=True)
def setup_test_env():
    # Setup test env (e.g. env vars)
    os.environ["SVR_ENV"] = "test"
    os.environ["SOVEREIGN_INTEGRITY_LEVEL"] = "0.95"
    os.environ["ANTIGRAVITY_GATEWAY_URL"] = "http://localhost:32553/mock"
    yield


@pytest.fixture
def mock_ollama(monkeypatch):
    """Mocks ollama library calls."""
    from unittest.mock import MagicMock

    mock = MagicMock()
    monkeypatch.setattr("ollama.chat", mock.chat)
    monkeypatch.setattr("ollama.embeddings", mock.embeddings)
    return mock


@pytest.fixture
def mock_gateway(monkeypatch):
    """Mocks GatewayArchitrave."""
    from unittest.mock import MagicMock

    mock = MagicMock()
    monkeypatch.setattr(
        "src.architrave.gateway_client.GatewayArchitrave", MagicMock(return_value=mock)
    )
    return mock
