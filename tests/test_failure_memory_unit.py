import pytest

from cognition.mnemosyne.reflection_store import ReflectionStore


# [SRC:axis_8]
@pytest.mark.asyncio
async def test_sqlite_failure_logic():
    store = ReflectionStore()

    # 1. Rule Validation Test (len < 50)
    short_rule = "Too short rule"
    res1 = store.store_failure("test_error", "root cause", short_rule)
    assert res1 == "", "Short rule should have been rejected"

    # 2. SHA-256 Dedup & Recurrence Test
    long_rule = "This is a very long prevention rule that exceeds fifty characters to pass the validation filter."
    hash1 = store.store_failure("duplicate_error", "cause A", long_rule)
    hash2 = store.store_failure("duplicate_error", "cause A", long_rule)

    assert hash1 == hash2, "Hashes should be identical for same error/cause"

    rules = store.get_prevention_rules(limit=10)
    found = [r for r in rules if r["prevention_rule"] == long_rule]
    assert len(found) > 0, "Rule should be stored"
    assert found[0]["recurrence_count"] >= 2, "Recurrence count should increment"
