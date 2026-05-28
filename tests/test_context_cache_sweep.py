"""
Unit tests for ContextCacheStore background sweep.
"""

import threading
import time

import pytest

from src.architrave.context_cache import ContextCacheStore


@pytest.fixture
def temp_db_path(tmp_path):
    return str(tmp_path / "temp_mnemosyne.db")


def test_context_cache_basic_ops(temp_db_path):
    # Disable auto background sweep for basic checks
    cache = ContextCacheStore(db_path=temp_db_path, start_sweep=False)
    try:
        # Initial state
        assert cache.count_active() == 0

        # Set cache key
        assert cache.set("test_data", ttl_seconds=10) is True
        assert cache.count_active() == 1
        assert cache.get("test_data") == "test_data"

        # Test cache hit / miss
        assert cache.get("non_existent") is None
    finally:
        cache.close()


def test_context_cache_background_sweep(temp_db_path):
    # Enable background sweep with custom fast check
    cache = ContextCacheStore(db_path=temp_db_path, start_sweep=True, sweep_interval=1.0)
    try:
        # Set expired key (ttl = -1 second)
        assert cache.set("expired_data", ttl_seconds=-1) is True
        # Set valid key
        assert cache.set("valid_data", ttl_seconds=60) is True

        # Background thread runs every second (due to the inner loop) or we can trigger it
        # Let's wait up to 1.5 seconds for the sweep thread to purge it
        time.sleep(1.5)

        # Expired data should be gone, valid data should remain
        assert cache.get("expired_data") is None
        assert cache.get("valid_data") == "valid_data"
        assert cache.count_active() == 1
    finally:
        cache.close()


def test_context_cache_multithreaded_load(temp_db_path):
    cache = ContextCacheStore(db_path=temp_db_path, start_sweep=True)
    try:

        def worker(idx):
            for i in range(20):
                content = f"data_{idx}_{i}"
                cache.set(content, ttl_seconds=60)
                cache.get(content)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert cache.count_active() == 100
    finally:
        cache.close()
