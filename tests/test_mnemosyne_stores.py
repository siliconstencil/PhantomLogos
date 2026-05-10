import pytest
from cognition.mnemosyne.episodic_store import EpisodicStore
from cognition.mnemosyne.goal_store import GoalStore
from cognition.mnemosyne.procedural_store import ProceduralStore
from cognition.mnemosyne.meta_cognition import MetaCognitionStore
from cognition.mnemosyne.rational_store import MnemosyneRationalStore

def test_episodic_store_basic():
    store = EpisodicStore(db_url="sqlite:///:memory:")
    store.log("session_1", "test_action", "test_result")
    recent = store.recent("session_1")
    assert len(recent) == 1
    assert recent[0]["action"] == "test_action"

def test_goal_store_basic():
    store = GoalStore(db_url="sqlite:///:memory:")
    store.add("Test Goal", "Description", priority=1)
    active = store.list_active()
    assert len(active) == 1
    assert active[0]["title"] == "Test Goal"

def test_rational_store_basic():
    store = MnemosyneRationalStore() # Uses secure_rules.json
    rules = store.get_secure_rules("system")
    assert isinstance(rules, list)

def test_procedural_store_import():
    store = ProceduralStore()
    assert store is not None

def test_meta_cognition_import():
    store = MetaCognitionStore()
    assert store is not None

if __name__ == "__main__":
    print("Running Mnemosyne Store tests...")
    test_episodic_store_basic()
    test_goal_store_basic()
    test_rational_store_basic()
    print("Mnemosyne Store tests passed.")
