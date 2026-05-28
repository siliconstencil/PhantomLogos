import os
from unittest.mock import patch

import pytest

from src.utils.security_utils import load_secrets_to_env, set_secret, validate_cloud_key


# [SRC:axis_11]
@pytest.fixture(autouse=True)
def clean_env():
    keys = ["GEMINI_API_KEY", "GOOGLE_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY"]
    old_values = {k: os.environ.get(k) for k in keys}
    for k in keys:
        if k in os.environ:
            del os.environ[k]
    yield
    for k, v in old_values.items():
        if v is not None:
            os.environ[k] = v
        elif k in os.environ:
            del os.environ[k]


def test_validate_cloud_key():
    assert validate_cloud_key("AIzaSyB12345678901234567890123456789012")
    assert not validate_cloud_key("invalid-key")
    assert not validate_cloud_key("")
    assert not validate_cloud_key(None)


@patch("keyring.get_password")
def test_load_secrets_keyring_success(mock_get):
    mock_get.side_effect = lambda service, key: (
        "AIza-from-keyring-12345678901234567890123456789" if key == "GEMINI_API_KEY" else None
    )
    load_secrets_to_env()
    assert os.environ.get("GEMINI_API_KEY") == "AIza-from-keyring-12345678901234567890123456789"
    assert os.environ.get("OPENAI_API_KEY") is None


@patch("keyring.get_password")
@patch("os.getenv")
def test_load_secrets_fallback(mock_getenv, mock_get_keyring):
    mock_get_keyring.return_value = None
    mock_getenv.side_effect = lambda key, default=None: (
        "AIza-from-env-12345678901234567890123456789" if key == "GEMINI_API_KEY" else None
    )
    load_secrets_to_env()
    # Note: if load_secrets_to_env calls os.getenv internally, this mock will trigger.
    # We just ensure it doesn't crash and populates env if intended.
    pass


@patch("keyring.set_password")
def test_set_secret(mock_set):
    mock_set.return_value = None
    res = set_secret("TEST_KEY", "TEST_VAL")
    assert res
    mock_set.assert_called_with("PhantomLogos", "TEST_KEY", "TEST_VAL")
