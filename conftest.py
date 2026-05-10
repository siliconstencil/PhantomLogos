import os
import sys
import pytest

# [SRC:axis_10]
# Ensure project root is in sys.path for test resolution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

@pytest.fixture(autouse=True)
def setup_test_env():
    """Ensure environment variables are set for tests."""
    os.environ["SVR_ENV"] = "test"
    # [SRC:axis_5] Database paths should be relative to project root
    yield
