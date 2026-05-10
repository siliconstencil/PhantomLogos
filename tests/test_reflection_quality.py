import pytest
from cognition.mnemosyne.reflection_store import ReflectionStore
import os

def test_reflection_quality_filter():
    store = ReflectionStore()
    session_id = "test_quality"
    
    # Too short
    res1 = store.store_reflection(session_id, "Short one")
    assert res1 is False
    
    # Long enough
    res2 = store.store_reflection(session_id, "This is a long enough insight that should be preserved for the future.")
    assert res2 is True

def test_entity_frequency():
    store = ReflectionStore()
    session_id = "test_freq"
    
    # First time
    store.store_entities(session_id, [{"text": "TestEntity", "type": "test"}])
    
    # Check frequency
    with store._get_conn() as conn:
        row = conn.execute("SELECT frequency FROM entities WHERE name='TestEntity'").fetchone()
        assert row[0] >= 1
        old_freq = row[0]
        
    # Second time
    store.store_entities(session_id, [{"text": "TestEntity", "type": "test"}])
    
    # Check increment
    with store._get_conn() as conn:
        row = conn.execute("SELECT frequency FROM entities WHERE name='TestEntity'").fetchone()
        assert row[0] == old_freq + 1

if __name__ == "__main__":
    test_reflection_quality_filter()
    test_entity_frequency()
    print("Reflection Quality & Entity Freq tests: PASSED")
