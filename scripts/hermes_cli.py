"""
Hermes CLI Bridge: Mnemosyne access for OpenCode/DeepSeek.
All operations are database-first -- no file output.
Usage: python scripts/hermes_cli.py <command> [args]
"""
import sys
import os
import json
import argparse
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _query_opencode_sessions(opencode_db: str) -> list:
    """Shared helper: query OpenCode DB via Axis 13 OpenCodeStore."""
    from src.architrave.opencode_store import OpenCodeStore
    store = OpenCodeStore(db_path=opencode_db)
    import datetime as _dt
    sessions = store.list_sessions(limit=10)
    for s in sessions:
        ts = s.get("time_created", 0)
        s["created_at"] = _dt.datetime.fromtimestamp(ts / 1000, tz=_dt.timezone.utc).isoformat() if ts else None
    return sessions


def cmd_init(args):
    """Create a new Hermes session in OperationalStore and return session_id."""
    from cognition.mnemosyne.operational_store import OperationalStore
    from cognition.mnemosyne.rational_store import MnemosyneRationalStore

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    session_id = f"hermes_{ts}"

    store = OperationalStore()
    store.record_event(
        name="hermes.session.init",
        level="INFO",
        message=f"Hermes session {session_id} started",
        agent_id="hermes",
        tool_name="hermes_cli",
    )

    rational = MnemosyneRationalStore()
    rational.add_fact("session_id", session_id, agent_id="hermes", predicate="active", source="hermes_cli")

    result = {"status": "active", "session_id": session_id, "created_at": ts}
    print(json.dumps(result))
    return 0


def cmd_load(args):
    """Load context for a session from Mnemosyne and optionally OpenCode DB."""
    from cognition.mnemosyne.episodic_store import EpisodicStore
    from cognition.mnemosyne.rational_store import MnemosyneRationalStore
    from cognition.mnemosyne.meta_cognition import MetaCognitionStore

    session_id = args.session
    result = {"session_id": session_id}

    # Mnemosyne: Episodic events
    try:
        eps = EpisodicStore()
        events = eps.recent(session_id, limit=5)
        result["recent_events"] = events
    except Exception as e:
        result["recent_events"] = {"error": str(e)}

    # Mnemosyne: Rational facts and rules
    try:
        rational = MnemosyneRationalStore()
        facts = rational.get_secure_facts("hermes")
        rules = rational.get_secure_rules("hermes")
        result["facts"] = facts
        result["rules"] = rules
    except Exception as e:
        result["facts"] = {"error": str(e)}

    # Mnemosyne: MetaCognition
    try:
        meta = MetaCognitionStore()
        reliability = meta.get_reliability("hermes")
        result["reliability"] = reliability
    except Exception as e:
        result["reliability"] = None

    opencode_db = getattr(args, 'opencode_db', None)
    try:
        from src.architrave.opencode_store import OpenCodeStore
        oc_store = OpenCodeStore(db_path=opencode_db)
        oc_sessions = oc_store.list_sessions(limit=5)
        if oc_sessions:
            result["opencode_sessions"] = oc_sessions
        
        # Axis 13: Patterns
        patterns = oc_store.get_cross_session_patterns()
        result["opencode_patterns"] = patterns
    except Exception as e:
        result["opencode_patterns"] = {"error": str(e)}

    print(json.dumps(result, default=str))
    return 0


def cmd_save(args):
    """Save data to Mnemosyne. --type fact|event|goal"""
    session_id = args.session
    data = None
    if hasattr(args, 'data') and args.data:
        try:
            data = json.loads(args.data)
        except json.JSONDecodeError:
            data = {"raw": args.data}

    if args.type == "fact":
        from cognition.mnemosyne.rational_store import MnemosyneRationalStore
        store = MnemosyneRationalStore()
        subject = getattr(args, 'subject', None) or (data.get("subject", "unnamed") if data else "unnamed")
        obj = getattr(args, 'object', None) or (data.get("object", "") if data else "")
        predicate = getattr(args, 'predicate', None) or (data.get("predicate", "is") if data else "is")
        store.add_fact(subject, obj, agent_id="hermes", predicate=predicate, source=f"session:{session_id}")
        result = {"status": "saved", "type": "fact", "subject": subject}

    elif args.type == "event":
        from cognition.mnemosyne.episodic_store import EpisodicStore
        from cognition.mnemosyne.operational_store import OperationalStore
        store = EpisodicStore()
        action = data.get("action", "unknown") if data else getattr(args, 'action', 'unknown')
        detail = data.get("detail", "") if data else ""
        store.log(session_id, action, agent_id="hermes", detail=detail, outcome=data.get("outcome", "pending") if data else "pending")
        op = OperationalStore()
        op.record_event(name=f"hermes.{action}", level="INFO", message=detail, agent_id="hermes")
        result = {"status": "saved", "type": "event", "action": action}

    elif args.type == "goal":
        from cognition.mnemosyne.goal_store import GoalStore
        store = GoalStore()
        title = data.get("title", "Untitled") if data else "Untitled"
        description = data.get("description", "") if data else ""
        priority = data.get("priority", 3) if data else 3
        gid = store.add(title, description, priority)
        result = {"status": "saved", "type": "goal", "goal_id": gid}

    else:
        result = {"error": f"Unknown type: {args.type}"}

    print(json.dumps(result, default=str))
    return 0


def cmd_search(args):
    """Search semantic memory for a session."""
    import numpy as np
    from cognition.mnemosyne.semantic_store import SemanticStore

    session_id = args.session
    query_text = args.query or ""

    store = SemanticStore()
    
    # O5: Use real embeddings via Ollama (Nomic Embed) instead of random stub
    try:
        from src.architrave.model_registry import get_embedding_model
        model_name = get_embedding_model()
        import ollama
        resp = ollama.embeddings(model=model_name, prompt=query_text)
        full_vec = np.array(resp.embedding)
        # Axis 6: Matryoshka 256-dim slicing
        vec = full_vec[:256]
    except Exception as e:
        logger.warning(f"cmd_search: Ollama embedding failed ({e}), returning empty results")
        output = {"session_id": session_id, "query": query_text, "error": f"Embedding failed: {e}", "results": []}
        print(json.dumps(output, default=str))
        return 0
    try:
        results = store.search(vec, session_id=session_id, limit=args.limit or 5)
        output = {"session_id": session_id, "query": query_text, "results": results}
        
        # Axis 13: Deep pattern analysis
        if getattr(args, 'deep', False):
            from src.architrave.opencode_store import OpenCodeStore
            oc_store = OpenCodeStore()
            patterns = oc_store.get_cross_session_patterns()
            output["deep_audit"] = {
                "axis": 13,
                "patterns": patterns,
                "recommendation": "High correlation with previous build patterns detected." if patterns.get("sessions", 0) > 10 else "Insufficient cross-session data."
            }
    except Exception as e:
        output = {"session_id": session_id, "query": query_text, "error": str(e), "results": []}

    print(json.dumps(output, default=str))
    return 0


def cmd_close(args):
    """Close a Hermes session."""
    from cognition.mnemosyne.operational_store import OperationalStore
    from cognition.mnemosyne.rational_store import MnemosyneRationalStore

    session_id = args.session
    store = OperationalStore()
    store.record_event(
        name="hermes.session.close",
        level="INFO",
        message=f"Hermes session {session_id} closed",
        agent_id="hermes",
        tool_name="hermes_cli",
    )

    rational = MnemosyneRationalStore()
    rational.add_fact("session_closed", session_id, agent_id="hermes", predicate="was", source="hermes_cli")

    result = {"status": "closed", "session_id": session_id}
    print(json.dumps(result))
    return 0


def cmd_list(args):
    """List recent Hermes sessions from OperationalStore + optional OpenCode DB."""
    from cognition.mnemosyne.operational_store import OperationalStore
    import sqlite3 as _sqlite

    store = OperationalStore()
    logs = store.get_recent_logs(limit=100)
    sessions = {}
    for log in logs:
        if log.agent_id != "hermes":
            continue
        if "hermes.session" in (log.name or ""):
            sid = (log.message or "").replace("Hermes session ", "").split()[0].strip()
            if sid not in sessions:
                sessions[sid] = {"init": None, "close": None}
            if "init" in (log.name or ""):
                sessions[sid]["init"] = log.timestamp.isoformat() if hasattr(log.timestamp, 'isoformat') else str(log.timestamp)
            elif "close" in (log.name or ""):
                sessions[sid]["close"] = log.timestamp.isoformat() if hasattr(log.timestamp, 'isoformat') else str(log.timestamp)

    result = []
    for sid in sorted(sessions.keys(), reverse=True):
        entry = {"session_id": sid}
        if sessions[sid]["init"]:
            entry["init_at"] = sessions[sid]["init"]
        if sessions[sid]["close"]:
            entry["closed_at"] = sessions[sid]["close"]
        result.append(entry)

    output = {"sessions": result, "count": len(result)}

    opencode_db = getattr(args, 'opencode_db', None)
    try:
        oc_sessions = _query_opencode_sessions(opencode_db)
        if oc_sessions:
            output["opencode_sessions"] = oc_sessions
    except Exception as e:
        output["opencode_sessions"] = {"error": str(e)}

    print(json.dumps(output, default=str))
    return 0


def main():
    parser = argparse.ArgumentParser(description="Hermes CLI Bridge: Mnemosyne access via bash")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_p = subparsers.add_parser("init", help="Create new Hermes session")
    init_p.set_defaults(func=cmd_init)

    load_p = subparsers.add_parser("load", help="Load context from Mnemosyne + optional OpenCode DB")
    load_p.add_argument("--session", required=True, help="Session ID to load")
    load_p.add_argument("--opencode-db", default=None, help="Path to OpenCode SQLite DB (D:\\opencode\\opencode.db)")
    load_p.set_defaults(func=cmd_load)

    save_p = subparsers.add_parser("save", help="Save data to Mnemosyne")
    save_p.add_argument("--session", required=True, help="Session ID")
    save_p.add_argument("--type", required=True, choices=["fact", "event", "goal"], help="Data type")
    save_p.add_argument("--data", default=None, help="JSON data string (alt: use --subject/--object)")
    save_p.add_argument("--subject", default=None, help="Fact subject (use with --type fact, avoids JSON)")
    save_p.add_argument("--object", default=None, help="Fact object")
    save_p.add_argument("--predicate", default=None, help="Fact predicate (default: is)")
    save_p.set_defaults(func=cmd_save)

    search_p = subparsers.add_parser("search", help="Search semantic memory")
    search_p.add_argument("--session", required=True, help="Session ID")
    search_p.add_argument("--query", default="", help="Search query text")
    search_p.add_argument("--limit", type=int, default=5, help="Max results")
    search_p.add_argument("--deep", action="store_true", help="Include Axis 13 deep pattern analysis")
    search_p.set_defaults(func=cmd_search)

    close_p = subparsers.add_parser("close", help="Close Hermes session")
    close_p.add_argument("--session", required=True, help="Session ID to close")
    close_p.set_defaults(func=cmd_close)

    list_p = subparsers.add_parser("list", help="List recent Hermes sessions + optional OpenCode DB")
    list_p.add_argument("--opencode-db", default=None, help="Path to OpenCode SQLite DB (D:\\opencode\\opencode.db)")
    list_p.set_defaults(func=cmd_list)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
