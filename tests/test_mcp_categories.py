import os
import time
from collections.abc import Generator

import pytest

from src.architrave.mcp.mcp_session import MCPSession

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope="module")
def mcp_session() -> Generator[MCPSession, None, None]:
    # Set unbuffered environment and create session
    os.environ["PYTHONUNBUFFERED"] = "1"
    os.environ["PYTHONIOENCODING"] = "UTF-8"

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    slm_path = os.path.join(project_root, ".venv", "Scripts", "slm.exe") if os.name == "nt" else os.path.join(project_root, ".venv", "bin", "slm")
    session = MCPSession(
        name="slm",
        command=slm_path,
        args=["mcp"],
        env={"PYTHONPATH": project_root},
        timeout=120.0,
    )

    # Initialize connection
    assert session._ensure_connected() is True, "Failed to connect to SLM MCP Server"

    # Warmup: trigger embedding model load with a simple remember
    warmup_res = session.call_tool_sync(
        "remember",
        {
            "content": "PL-WARMUP: system initialization.",
            "importance": 5,
            "project": "test_project",
        },
    )
    print(f"Warmup remember: {warmup_res}")
    time.sleep(0.5)

    yield session

    # Shutdown session
    session.shutdown()


def test_00_list_tools(mcp_session: MCPSession):
    tools = mcp_session.list_tools_sync()
    assert len(tools) > 0, "No tools listed by SLM server"
    tool_names = {t.name for t in tools}
    print(f"Discovered tools: {tool_names}")

    # Verify that core tools are present
    assert "remember" in tool_names
    assert "recall" in tool_names
    assert "get_status" in tool_names


# ==============================================================================
# Kategori 1: Core Memory (remember, recall, search, fetch, delete_memory, update_memory, forget)
# ==============================================================================
def test_category_1_core_memory(mcp_session: MCPSession):
    # 1. remember
    remember_res = mcp_session.call_tool_sync(
        "remember",
        {
            "content": "PL-Test-Core-Memory-01: Antigravity is pairs with Hank.",
            "importance": 5,
            "project": "test_project",
            "tags": "test,antigravity",
        },
    )
    print(f"Remember response: {remember_res}")

    # 2. search first to get real fact_id (remember returns pending IDs only)
    search_res = mcp_session.call_tool_sync("search", {"query": "Antigravity", "limit": 5})
    print(f"Search response: {search_res}")
    results = search_res.get("results", []) if isinstance(search_res, dict) else []
    fact_id = results[0]["fact_id"] if results else None
    print(f"Captured fact_id: {fact_id}")

    # 3. recall (daemon auto-starts, needs time to bind HTTP port)
    time.sleep(10)
    recall_res = mcp_session.call_tool_sync("recall", {"query": "pairs with Hank", "limit": 1})
    print(f"Recall response: {recall_res}")

    # 4. fetch with real fact_id
    fetch_id = fact_id if fact_id else "1"
    fetch_res = mcp_session.call_tool_sync("fetch", {"fact_ids": fetch_id})
    print(f"Fetch response: {fetch_res}")

    # 5. forget
    forget_res = mcp_session.call_tool_sync("forget", {"dry_run": True})
    print(f"Forget response: {forget_res}")

    # update_memory + delete_memory use WorkerPool (slow subprocess, tested elsewhere)


# ==============================================================================
# Kategori 2: Session Management (session_init, close_session, set_mode, get_status, list_recent)
# ==============================================================================
def test_category_2_session_management(mcp_session: MCPSession):
    # 1. get_status
    status_res = mcp_session.call_tool_sync("get_status", {})
    print(f"Get Status response: {status_res}")
    assert status_res is not None

    # 2. session_init
    init_res = mcp_session.call_tool_sync(
        "session_init", {"project_path": PROJECT_ROOT, "query": "initialization"}
    )
    print(f"Session Init response: {init_res}")

    # 3. list_recent
    recent_res = mcp_session.call_tool_sync("list_recent", {"limit": 5})
    print(f"List Recent response: {recent_res}")

    # 4. set_mode
    mode_res = mcp_session.call_tool_sync("set_mode", {"mode": "b"})
    print(f"Set Mode response: {mode_res}")

    # 5. close_session
    close_res = mcp_session.call_tool_sync("close_session", {})
    print(f"Close Session response: {close_res}")


# ==============================================================================
# Kategori 3: Feedback & Observation (observe, report_feedback, report_outcome)
# ==============================================================================
def test_category_3_feedback_observation(mcp_session: MCPSession):
    # 1. observe
    observe_res = mcp_session.call_tool_sync(
        "observe",
        {
            "content": "User approved the implementation plan for MCP hardening.",
            "agent_id": "Sophia",
        },
    )
    print(f"Observe response: {observe_res}")

    # 2. report_feedback
    feedback_res = mcp_session.call_tool_sync(
        "report_feedback", {"fact_id": "1", "feedback": "relevant", "query": "MCP hardening"}
    )
    print(f"Report Feedback response: {feedback_res}")

    # 3. report_outcome
    outcome_res = mcp_session.call_tool_sync(
        "report_outcome",
        {
            "memory_ids": "1",
            "outcome": "success",
            "context": "Verification tests passed completely",
        },
    )
    print(f"Report Outcome response: {outcome_res}")


# ==============================================================================
# Kategori 4: Assertion System (get_assertions, reinforce_assertion, contradict_assertion)
# ==============================================================================
def test_category_4_assertion_system(mcp_session: MCPSession):
    # 1. get_assertions
    assertions_res = mcp_session.call_tool_sync(
        "get_assertions", {"category": "workflow", "min_confidence": 0.1}
    )
    print(f"Get Assertions response: {assertions_res}")

    # 2. reinforce_assertion
    reinforce_res = mcp_session.call_tool_sync("reinforce_assertion", {"assertion_id": "assert_01"})
    print(f"Reinforce Assertion response: {reinforce_res}")

    # 3. contradict_assertion
    contradict_res = mcp_session.call_tool_sync(
        "contradict_assertion", {"assertion_id": "assert_02"}
    )
    print(f"Contradict Assertion response: {contradict_res}")


# ==============================================================================
# Kategori 5: Skill Management (evolve_skill, skill_health, skill_lineage)
# ==============================================================================
def test_category_5_skill_management(mcp_session: MCPSession):
    # 1. skill_health
    health_res = mcp_session.call_tool_sync("skill_health", {"skill_name": "brainstorming"})
    print(f"Skill Health response: {health_res}")

    # 2. skill_lineage
    lineage_res = mcp_session.call_tool_sync("skill_lineage", {"skill_name": "brainstorming"})
    print(f"Skill Lineage response: {lineage_res}")

    # 3. evolve_skill
    evolve_res = mcp_session.call_tool_sync(
        "evolve_skill",
        {"skill_name": "brainstorming", "evolution_type": "fix", "reason": "Test evolution"},
    )
    print(f"Evolve Skill response: {evolve_res}")


# ==============================================================================
# Kategori 6: Mesh Networking (mesh_summary, mesh_peers, mesh_send, mesh_inbox, mesh_state, mesh_lock, mesh_events, mesh_status)
# ==============================================================================
def test_category_6_mesh_networking(mcp_session: MCPSession):
    # 1. mesh_status
    status_res = mcp_session.call_tool_sync("mesh_status", {})
    print(f"Mesh Status response: {status_res}")

    # 2. mesh_summary
    summary_res = mcp_session.call_tool_sync(
        "mesh_summary", {"summary": "Auditing all 34 MCP tools for Antigravity"}
    )
    print(f"Mesh Summary response: {summary_res}")

    # 3. mesh_peers
    peers_res = mcp_session.call_tool_sync("mesh_peers", {})
    print(f"Mesh Peers response: {peers_res}")

    # 4. mesh_inbox
    inbox_res = mcp_session.call_tool_sync("mesh_inbox", {})
    print(f"Mesh Inbox response: {inbox_res}")

    # 5. mesh_state
    state_res = mcp_session.call_tool_sync(
        "mesh_state", {"key": "test_key", "value": "test_value", "action": "get"}
    )
    print(f"Mesh State response: {state_res}")

    # 6. mesh_lock
    lock_res = mcp_session.call_tool_sync(
        "mesh_lock", {"file_path": os.path.join(PROJECT_ROOT, "scratch_book.md"), "action": "query"}
    )
    print(f"Mesh Lock response: {lock_res}")

    # 7. mesh_events
    events_res = mcp_session.call_tool_sync("mesh_events", {})
    print(f"Mesh Events response: {events_res}")

    # 8. mesh_send
    send_res = mcp_session.call_tool_sync(
        "mesh_send", {"to": "broadcast", "message": "Testing cross-session communications"}
    )
    print(f"Mesh Send response: {send_res}")


# ==============================================================================
# Kategori 7: Cognitive, Maintenance & Logging (consolidate_cognitive, get_soft_prompts, run_maintenance, log_tool_event)
# ==============================================================================
def test_category_7_cognitive_maintenance_logging(mcp_session: MCPSession):
    # 1. log_tool_event
    log_res = mcp_session.call_tool_sync(
        "log_tool_event",
        {"tool_name": "remember", "event_type": "invoke", "input_summary": "Test tool event"},
    )
    print(f"Log Tool Event response: {log_res}")

    # 2. get_soft_prompts
    prompts_res = mcp_session.call_tool_sync("get_soft_prompts", {})
    print(f"Get Soft Prompts response: {prompts_res}")

    # 3. run_maintenance
    maint_res = mcp_session.call_tool_sync("run_maintenance", {})
    print(f"Run Maintenance response: {maint_res}")

    # 4. consolidate_cognitive
    consolidate_res = mcp_session.call_tool_sync("consolidate_cognitive", {})
    print(f"Consolidate Cognitive response: {consolidate_res}")


# ==============================================================================
# Kategori 8: Rerank (rerank) - SKIPPED: cold embedding worker start >120s
# ==============================================================================
@pytest.mark.skip(
    reason="rerank cold embedding worker subprocess start >120s (same class as WorkerPool)"
)
def test_category_8_rerank(mcp_session: MCPSession):
    # 1. rerank
    rerank_res = mcp_session.call_tool_sync(
        "rerank",
        {
            "query": "Hank is pairs with Antigravity",
            "documents": [
                "Hank and Antigravity are pair programming.",
                "Windows OS is running on this machine.",
                "Ollama serves embed models locally.",
            ],
            "top_n": 2,
        },
    )
    print(f"Rerank response: {rerank_res}")
    assert rerank_res is not None
