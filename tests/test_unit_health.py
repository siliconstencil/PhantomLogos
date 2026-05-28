import os
import time
from unittest.mock import MagicMock, PropertyMock, patch


class TestProjectPath:
    def test_get_project_root_returns_path(self):
        from src.utils.project_path import get_project_root

        root = get_project_root()
        assert root.exists()
        assert (root / "src").is_dir()
        assert (root / "cognition").is_dir()

    def test_to_absolute_path_resolves_correctly(self):
        from src.utils.project_path import get_project_root, to_absolute_path

        result = to_absolute_path("data/test.db")
        expected = str(get_project_root() / "data/test.db")
        assert result == expected

    def test_to_absolute_path_handles_subdirs(self):
        from src.utils.project_path import to_absolute_path

        result = to_absolute_path("src/clotho/orchestrator.py")
        assert result.endswith("orchestrator.py")
        assert "clotho" in result


class TestProceduralStore:
    def test_record_usage_creates_new(self, tmp_path):
        db_url = f"sqlite:///{tmp_path / 'test_procedural.db'}"
        from cognition.mnemosyne.procedural_store import ProceduralStore

        store = ProceduralStore(db_url=db_url)
        rid = store.record_usage("test_tool", "test_task", success=True, latency_ms=100)
        assert rid is None
        best = store.best_tool("test_task")
        assert len(best) == 1
        name, rate, lat = best[0]
        assert name == "test_tool"
        assert rate == 1.0
        assert lat == 100

    def test_record_usage_updates_existing(self, tmp_path):
        db_url = f"sqlite:///{tmp_path / 'test_procedural2.db'}"
        from cognition.mnemosyne.procedural_store import ProceduralStore

        store = ProceduralStore(db_url=db_url)
        store.record_usage("tool_a", "task_x", success=True, latency_ms=50)
        store.record_usage("tool_a", "task_x", success=False, latency_ms=200)
        best = store.best_tool("task_x")
        assert len(best) == 1
        name, rate, lat = best[0]
        assert rate == 0.5
        assert lat == 125

    def test_best_tool_returns_sorted_by_success_rate(self, tmp_path):
        db_url = f"sqlite:///{tmp_path / 'test_procedural3.db'}"
        from cognition.mnemosyne.procedural_store import ProceduralStore

        store = ProceduralStore(db_url=db_url)
        store.record_usage("tool_low", "task", success=True, latency_ms=10)
        store.record_usage("tool_low", "task", success=False, latency_ms=10)
        store.record_usage("tool_high", "task", success=True, latency_ms=10)
        best = store.best_tool("task")
        assert best[0][0] == "tool_high"
        assert best[0][1] == 1.0

    def test_best_tool_empty_task(self, tmp_path):
        db_url = f"sqlite:///{tmp_path / 'test_procedural4.db'}"
        from cognition.mnemosyne.procedural_store import ProceduralStore

        store = ProceduralStore(db_url=db_url)
        assert store.best_tool("nonexistent") == []


class TestGoalStore:
    def test_add_and_list_active(self, tmp_path):
        db_url = f"sqlite:///{tmp_path / 'test_goals.db'}"
        from cognition.mnemosyne.goal_store import GoalStore

        store = GoalStore(db_url=db_url)
        gid = store.add("Test Goal", "A test goal", priority=1)
        assert gid is not None
        active = store.list_active()
        assert len(active) >= 1
        titles = [g["title"] for g in active]
        assert "Test Goal" in titles

    def test_complete_goal(self, tmp_path):
        db_url = f"sqlite:///{tmp_path / 'test_goals2.db'}"
        from cognition.mnemosyne.goal_store import GoalStore

        store = GoalStore(db_url=db_url)
        gid = store.add("Complete Me", "Will be done")
        store.complete(gid)
        active = store.list_active()
        assert all(g["id"] != gid for g in active)

    def test_update_progress(self, tmp_path):
        db_url = f"sqlite:///{tmp_path / 'test_goals3.db'}"
        from cognition.mnemosyne.goal_store import GoalStore

        store = GoalStore(db_url=db_url)
        gid = store.add("Progress Goal")
        store.update_progress(gid, 50)
        store.update_progress(gid, 100)
        active = store.list_active()
        assert all(g["id"] != gid for g in active)

    def test_list_active_respects_limit(self, tmp_path):
        db_url = f"sqlite:///{tmp_path / 'test_goals4.db'}"
        from cognition.mnemosyne.goal_store import GoalStore

        store = GoalStore(db_url=db_url)
        for i in range(5):
            store.add(f"Goal {i}", priority=3)
        active = store.list_active(limit=2)
        assert len(active) == 2


class TestTokenBudgetGuard:
    def test_consume_within_limits(self):
        from src.atropos.token_budget import TokenBudgetGuard

        guard = TokenBudgetGuard(daily_limit=1000, hourly_limit=100, session_id="test_unit")
        assert guard.consume(50) is True
        assert guard.remaining_daily() == 950
        assert guard.remaining_hourly() == 50

    def test_consume_exceeds_hourly(self):
        from src.atropos.token_budget import TokenBudgetGuard

        guard = TokenBudgetGuard(daily_limit=10000, hourly_limit=100, session_id="test_unit2")
        assert guard.consume(60) is True
        assert guard.consume(50) is False
        assert guard.remaining_daily() == 9940

    def test_consume_exceeds_daily(self):
        from src.atropos.token_budget import TokenBudgetGuard

        guard = TokenBudgetGuard(daily_limit=100, hourly_limit=10000, session_id="test_unit3")
        assert guard.consume(60) is True
        assert guard.consume(50) is False

    def test_status_structure(self):
        from src.atropos.token_budget import TokenBudgetGuard

        guard = TokenBudgetGuard(daily_limit=500, hourly_limit=50, session_id="test_unit4")
        guard.consume(30)
        s = guard.status()
        assert s["daily_used"] == 30
        assert s["daily_remaining"] == 470
        assert s["hourly_used"] == 30
        assert s["hourly_remaining"] == 20

    def test_remaining_returns_non_negative(self):
        from src.atropos.token_budget import TokenBudgetGuard

        guard = TokenBudgetGuard(daily_limit=50, hourly_limit=50, session_id="test_unit5")
        assert guard.consume(51) is False
        assert guard.remaining_daily() == 50

    def test_get_token_guard_singleton(self):
        from src.atropos.token_budget import get_token_guard

        g1 = get_token_guard(50000)
        g2 = get_token_guard(50000)
        assert g1 is g2


class TestMemoryLeakMonitor:
    def test_start_and_check(self):
        from cognition.morpheus.monitor import MemoryLeakMonitor

        monitor = MemoryLeakMonitor(top_n=3, interval_s=1)
        monitor.start()
        leaks = monitor.check()
        assert isinstance(leaks, list)

    def test_should_warn_no_leak(self):
        from cognition.morpheus.monitor import MemoryLeakMonitor

        monitor = MemoryLeakMonitor()
        assert monitor.should_warn([]) is False

    def test_should_warn_small_leak(self):
        from cognition.morpheus.monitor import MemoryLeakMonitor

        monitor = MemoryLeakMonitor()
        small_leaks = [{"size_diff_b": 1024}]
        assert monitor.should_warn(small_leaks, threshold_b=1048576) is False

    def test_should_warn_large_leak(self):
        from cognition.morpheus.monitor import MemoryLeakMonitor

        monitor = MemoryLeakMonitor()
        large_leaks = [{"size_diff_b": 2097152}]
        assert monitor.should_warn(large_leaks, threshold_b=1048576) is True
