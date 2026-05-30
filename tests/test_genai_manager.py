import os
import sys
import time
from unittest.mock import patch

import pytest

# Add project root to sys.path to allow importing from scripts
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.genai_manager import sync_cache


def test_sync_cache_unauthorized():
    # Remove L0 token or mock it to be expired
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    token_path = os.path.join(project_root, "data", "snapshots", "L0_AUTH_TOKEN")

    with patch("os.path.exists", return_value=False):
        with pytest.raises(SystemExit) as excinfo:
            sync_cache([])
        assert excinfo.value.code == 1


def test_sync_cache_authorized_mock():
    # Mock token to exist and be valid
    with (
        patch("os.path.exists", return_value=True),
        patch("os.stat") as mock_stat,
        patch("google.genai.Client") as mock_client,
    ):
        mock_stat.return_value.st_mtime = time.time()

        # We expect sync_cache to run client initialization
        sync_cache([])

        # Assert client was created with base_url pointing to gateway
        mock_client.assert_called_once()
        _args, kwargs = mock_client.call_args
        assert kwargs.get("api_key") == "antigravity-native"
        assert kwargs.get("http_options").base_url == os.getenv(
            "ANTIGRAVITY_GATEWAY_URL", "http://localhost:32553"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
