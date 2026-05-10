import os
import sys
import pytest
import asyncio

# [SRC:axis_10]
# Ensure project root is in path for all tests to resolve imports without path_insert
sys.path.append(os.getcwd())

# [SRC:axis_10]
# Ensure project root is in path for all tests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

@pytest.fixture(autouse=True)
def setup_test_env():
    # Setup test env (e.g. env vars)
    os.environ["Sovereign_INTEGRITY_LEVEL"] = "0.95"
    yield
