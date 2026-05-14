import logging
import sys
from pathlib import Path

# Add project root to path
root = Path(__file__).resolve().parent.parent
sys.path.append(str(root))

# Mock logging to avoid SQLite hangs during test
import src.utils.logging_config

src.utils.logging_config.setup_logger = lambda name: logging.getLogger(name)
logging.basicConfig(level=logging.INFO)

from cognition.mnemosyne.meta_cognition import _RELIABILITY_CACHE, MetaCognitionStore


def test_cache():
    print("=== Testing Reliability Cache Fallback (No-DB Mode) ===")

    # Manually populate the process-level cache
    agent = "test_agent_115"
    _RELIABILITY_CACHE[agent] = 0.85
    print(f"Manual Cache Setup: {agent} = 0.85")

    # Instantiate store (should not hang now with mocked logger)
    # We pass dummy URLs to avoid file creation
    store = MetaCognitionStore(db_url="sqlite:///:memory:", reliability_db="sqlite:///:memory:")

    # 2. Simulate DB Failure by setting engine to None
    store._reliability_engine = None

    # 3. Request - should catch AttributeError and use cache
    print(f"Requesting {agent} with 'broken' DB...")
    fallback_score = store.get_reliability(agent)
    print(f"Result: {fallback_score}")

    if fallback_score == 0.85:
        print("SUCCESS: Cache fallback verified.")
        return True
    else:
        print(f"FAILED: Expected 0.85, got {fallback_score}")
        return False


if __name__ == "__main__":
    success = test_cache()
    sys.exit(0 if success else 1)
