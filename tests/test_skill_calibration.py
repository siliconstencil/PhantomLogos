import asyncio

import pytest

from src.clotho.ergon.symmachia import negotiate_node


@pytest.mark.asyncio
async def test_skill_calibration_audit():
    state = {
        "task": "Perform a security audit on the persistence layer",
        "session_id": "test_session_1",
    }
    result = await negotiate_node(state)

    assert "calibrated_skills" in result
    assert "security-audit" in result["calibrated_skills"]
    assert "persona-auditor" in result["calibrated_skills"]
    print("\n[SUCCESS] Audit task calibrated correctly.")


@pytest.mark.asyncio
async def test_skill_calibration_refactor():
    state = {
        "task": "Refactor the circular dependencies in service_locator",
        "session_id": "test_session_2",
    }
    result = await negotiate_node(state)

    assert "calibrated_skills" in result
    assert "code-generation" in result["calibrated_skills"]
    assert "logic-deadlock-resolver" in result["calibrated_skills"]
    print("\n[SUCCESS] Refactor task calibrated correctly.")


@pytest.mark.asyncio
async def test_skill_calibration_default():
    state = {"task": "Just a normal chat", "session_id": "test_session_3"}
    result = await negotiate_node(state)

    assert "calibrated_skills" in result
    assert "error-self-recovery" in result["calibrated_skills"]
    print("\n[SUCCESS] Default task calibrated correctly.")


if __name__ == "__main__":
    asyncio.run(test_skill_calibration_audit())
    asyncio.run(test_skill_calibration_refactor())
    asyncio.run(test_skill_calibration_default())
