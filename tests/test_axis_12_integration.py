import os
import sqlite3

import pytest

from cognition.sophia.gnosis.axis_12_cache import _build_axis_12
from src.architrave.nomos import log_cache_metrics as _log_cache_metrics


@pytest.fixture
def clean_axis_12_db():
    """Ensure a clean database for testing cache metrics."""
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base, "data", "mnemosyne.db")

    # Backup existing database or modify in-place
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("DROP TABLE IF EXISTS axis_12_cache_metrics")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS axis_12_cache_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                session_id VARCHAR(64) NOT NULL,
                prompt_hash VARCHAR(64),
                cached_tokens INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0,
                latency_ms FLOAT DEFAULT 0.0,
                hit_status VARCHAR(20) NOT NULL
            )
        """)
        conn.commit()
    finally:
        conn.close()
    yield db_path


def test_log_cache_metrics_helper(clean_axis_12_db):
    """Test that _log_cache_metrics helper successfully writes to the SQLite database."""
    session_id = "test_metrics_session"
    prompt = "SELECT * FROM system_rules WHERE active = 1"

    # Mock GenAI's usage_metadata response
    class MockUsageMetadata:
        def __init__(self, cached_content_token_count, prompt_token_count, total_token_count):
            self.cached_content_token_count = cached_content_token_count
            self.prompt_token_count = prompt_token_count
            self.total_token_count = total_token_count

    # 1. Test standard Hit
    usage_hit = MockUsageMetadata(
        cached_content_token_count=1000, prompt_token_count=1000, total_token_count=1200
    )
    _log_cache_metrics(session_id, prompt, usage_hit, 150.0)

    # 2. Test Partial hit
    usage_partial = MockUsageMetadata(
        cached_content_token_count=400, prompt_token_count=1000, total_token_count=1200
    )
    _log_cache_metrics(session_id, prompt, usage_partial, 200.0)

    # 3. Test Miss
    usage_miss = MockUsageMetadata(
        cached_content_token_count=0, prompt_token_count=1000, total_token_count=1200
    )
    _log_cache_metrics(session_id, prompt, usage_miss, 350.0)

    # Verify database contents
    conn = sqlite3.connect(clean_axis_12_db)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT cached_tokens, total_tokens, latency_ms, hit_status FROM axis_12_cache_metrics WHERE session_id = ?",
            (session_id,),
        )
        rows = cursor.fetchall()

        assert len(rows) == 3

        # Row 1: Hit
        assert rows[0][0] == 1000
        assert rows[0][1] == 1200
        assert rows[0][2] == 150.0
        assert rows[0][3] == "hit"

        # Row 2: Partial
        assert rows[1][0] == 400
        assert rows[1][1] == 1200
        assert rows[1][2] == 200.0
        assert rows[1][3] == "partial"

        # Row 3: Miss
        assert rows[2][0] == 0
        assert rows[2][1] == 1200
        assert rows[2][2] == 350.0
        assert rows[2][3] == "miss"
    finally:
        conn.close()


def test_build_axis_12_reflection(clean_axis_12_db):
    """Test that _build_axis_12 correctly aggregates and formats cache metrics for Sophia."""
    session_id = "test_reflection_session"

    # Inject test metrics
    conn = sqlite3.connect(clean_axis_12_db)
    try:
        conn.execute(
            """
            INSERT INTO axis_12_cache_metrics (session_id, prompt_hash, cached_tokens, total_tokens, latency_ms, hit_status)
            VALUES (?, 'hash1', 800, 1000, 100.0, 'partial')
        """,
            (session_id,),
        )
        conn.execute(
            """
            INSERT INTO axis_12_cache_metrics (session_id, prompt_hash, cached_tokens, total_tokens, latency_ms, hit_status)
            VALUES (?, 'hash2', 1000, 1200, 80.0, 'hit')
        """,
            (session_id,),
        )
        conn.commit()
    finally:
        conn.close()

    # Call _build_axis_12
    feedback = _build_axis_12(session_id)

    # Assert output formatting
    assert "### MNEMOSYNE AXIS 12 (EFFICIENCY/CACHE)" in feedback
    assert "Session Caching: Requests=2" in feedback
    assert "CachedTokens=1800" in feedback
    assert "TotalTokens=2200" in feedback

    # Expected hit rate: (1800/2200) * 100 = 81.8%
    assert "HitRate=81.8%" in feedback

    # Expected avg latency: (100 + 80) / 2 = 90ms
    assert "AvgLatency=90.0ms" in feedback

    # Check hit distribution reflection
    assert "Cache Hit Distribution:" in feedback
    assert "partial=1" in feedback
    assert "hit=1" in feedback
