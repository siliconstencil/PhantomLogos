"""Integration coverage for the SuperLocalMemory HTTP transport.

SuperLocalMemory is an optional full-memory mode. The daemon exposes
/health, /remember, /recall and /observe over HTTP on port 8765; the MCP stdio
path is retired. These tests therefore drive the project's own SLMClient and
skip when the daemon is not running.
"""

import os
import time

import pytest

from src.architrave.mcp import get_slm_client

pytestmark = pytest.mark.integration

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope="module")
def slm_client():
    client = get_slm_client()
    if not client.health():
        pytest.skip("The SuperLocalMemory daemon does not answer on port 8765")
    return client


def test_00_health(slm_client):
    assert slm_client.health() is True


def test_category_1_core_memory(slm_client):
    text = "PL-Test-Core-Memory-01: Phantom Logos runs on Linux and Windows."

    assert slm_client.remember({"text": text}, table_name="test_project") is True

    results = slm_client.search("Phantom Logos runs on Linux", limit=5)
    assert isinstance(results, list)
    assert results, "the daemon returned no recall result for a stored memory"
    assert "text" in results[0]


def test_category_2_session_management(slm_client):
    assert slm_client.session_init(project_path=PROJECT_ROOT, query="initialization") == {}


def test_category_3_feedback_observation(slm_client):
    assert slm_client.observe("User approved the implementation plan for MCP hardening.") is True
    time.sleep(0.5)


def test_category_7_cognitive_maintenance_logging(slm_client):
    # The HTTP daemon has no maintenance endpoints; the client must degrade
    # gracefully instead of raising.
    assert slm_client.embed("no embed endpoint") == []
    assert slm_client.rerank("query", ["a", "b"], top_n=1) == {"results": []}
