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
# modules are collected. The scratch directory lives inside the project so that
# nothing is written to the system temp directory.
from src.utils.project_path import get_project_root

_SCRATCH_ROOT = get_project_root() / "tmp"
_SCRATCH_ROOT.mkdir(parents=True, exist_ok=True)
_TEST_DATA_DIR = tempfile.mkdtemp(prefix="phantom-test-data-", dir=str(_SCRATCH_ROOT))
os.environ["PHANTOM_DATA_DIR"] = _TEST_DATA_DIR
atexit.register(shutil.rmtree, _TEST_DATA_DIR, True)

# Test modules that need a local model, a GPU or a live external server. They are
# marked so that the CI unit job leaves them out and the scheduled job runs them
# separately.
ENVIRONMENT_DEPENDENT_MODULES = frozenset(
    {
        "test_a2a_federation.py",
        "test_ankyra_v2.py",
        "test_full_pipeline.py",
        "test_gateway_circuit_breaker.py",
        "test_gateway_distillation.py",
        "test_gateway_secondary.py",
        "test_genai_manager.py",
        "test_gnosis.py",
        "test_hermes_bridge.py",
        "test_langgraph_checkpoint_persistence.py",
        "test_mcp_categories.py",
        "test_skill_calibration.py",
        "test_slm_fallback.py",
        "test_slm_rerank.py",
        "test_sophia_routing.py",
        "test_tool_bridge.py",
    }
)


def _ollama_reachable() -> bool:
    """True when a local Ollama server answers on the configured host."""
    import urllib.error
    import urllib.request

    base = os.getenv("OLLAMA_BASE_URL") or os.getenv("OLLAMA_HOST") or "http://127.0.0.1:11434"
    if not base.startswith("http"):
        base = f"http://{base}"
    try:
        with urllib.request.urlopen(  # noqa: S310
            f"{base.rstrip('/')}/api/version", timeout=2.0
        ) as response:
            return response.status == 200
    except (urllib.error.URLError, OSError, ValueError):
        return False


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Mark the environment dependent modules and skip them when Ollama is absent."""
    for item in items:
        if item.path.name in ENVIRONMENT_DEPENDENT_MODULES:
            item.add_marker(pytest.mark.integration)

    if _ollama_reachable():
        return
    skip = pytest.mark.skip(
        reason="Ollama is not reachable; this test needs a local model server"
    )
    for item in items:
        if "integration" in item.keywords or "slow" in item.keywords:
            item.add_marker(skip)


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
