

from cognition.sophia.tool_validator import ToolValidator
from cognition.sophia.temperature_control import get_temperature, TEMPERATURE_PROFILES
import pytest


def test_valid_json():
    tv = ToolValidator()
    data = tv.validate_json('{"is_valid": true, "flaws": ["bug1"]}', ["is_valid", "flaws"])
    assert data["is_valid"] is True
    assert "bug1" in data["flaws"]


def test_missing_keys():
    tv = ToolValidator()
    with pytest.raises(ValueError):
        tv.validate_json('{"x": 1}', ["is_valid"])


def test_non_json():
    tv = ToolValidator(max_retries=0)
    with pytest.raises(ValueError):
        tv.validate_json("not json at all", ["is_valid"])


def test_all_temperatures():
    for role in TEMPERATURE_PROFILES:
        t = get_temperature(role)
        assert 0.0 <= t <= 1.0, f"Invalid temperature {t} for role {role}"
    assert get_temperature("unknown") == 0.3


if __name__ == "__main__":
    print("=== Tool Validator & Temperature Test ===")
    test_valid_json()
    test_all_temperatures()
    print("Running missing key test...")
    try:
        test_missing_keys()
    except ValueError:
        print("  Missing keys correctly rejected")
    print("Running non-JSON test...")
    try:
        test_non_json()
    except ValueError:
        print("  Non-JSON correctly rejected")
    print("All validator tests passed.")
