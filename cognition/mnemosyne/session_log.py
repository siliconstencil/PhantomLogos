import json
from typing import Any

from src.utils.logging_config import setup_logger

from .episodic_store import EpisodicStore

logger = setup_logger(__name__)


class SessionLog:
    """
    SOTA 2026 Durable Session Event Log.
    Managed Agents pattern: session is the source of truth for context.
    """

    def __init__(self, session_id: str, store: EpisodicStore | None = None):
        self.session_id = session_id
        self.store = store or EpisodicStore()
        self._current_seq = -1

    def append(self, event_type: str, payload: dict[str, Any], agent_id: str = "system") -> int:
        seq = self.store.log_event(
            self.session_id, event_type, json.dumps(payload), agent_id=agent_id
        )
        if seq >= 0:
            self._current_seq = seq
            logger.info(f"SessionLog [{self.session_id}]: Appended {event_type} (seq={seq})")
        return seq

    def get_history(self, limit: int = 100) -> list[dict[str, Any]]:
        events = self.store.get_events(self.session_id, limit=limit)
        return [
            {
                "seq_num": e.seq_num,
                "type": e.event_type,
                "agent": e.agent_id,
                "payload": json.loads(e.payload) if e.payload else {},
                "timestamp": e.created_at.isoformat(),
            }
            for e in events
        ]

    def wake(self) -> dict[str, Any]:
        history = self.get_history(limit=500)
        if not history:
            return {"status": "new", "last_seq": -1}
        last_event = history[-1]
        return {
            "status": "recovered",
            "last_seq": last_event["seq_num"],
            "last_type": last_event["type"],
            "event_count": len(history),
        }

    def compact(self, max_tokens: int = 8000) -> dict[str, Any]:
        history = self.get_history(limit=2000)
        if len(history) < 10:
            return {"summary": "", "event_count": len(history), "truncated": False}
        header = history[:5]
        recent = history[-5:]
        middle = history[5:-5]
        task_events = [e for e in middle if e["type"].startswith("task.")]
        tool_events = [e for e in middle if e["type"].startswith("tool.")]
        audit_events = [e for e in middle if e["type"].startswith("evaluator.")]
        errors = [e for e in middle if "error" in str(e.get("payload", {})).lower()]
        summary_parts = []
        if task_events:
            tasks = [
                e["payload"].get("objective", "")[:120]
                for e in task_events
                if isinstance(e.get("payload"), dict)
            ]
            summary_parts.append(f"Tasks processed ({len(task_events)}): {'; '.join(tasks[:3])}")
        if tool_events:
            tool_names = set()
            for e in tool_events:
                p = e.get("payload", {})
                if isinstance(p, dict):
                    tool_names.add(p.get("tool", "unknown"))
            summary_parts.append(
                f"Tools used ({len(tool_events)} calls): {', '.join(sorted(tool_names))}"
            )
        if audit_events:
            scores = []
            for e in audit_events:
                p = e.get("payload", {})
                if isinstance(p, dict) and "overall_score" in p:
                    scores.append(p["overall_score"])
            avg = sum(scores) / len(scores) if scores else 0
            summary_parts.append(f"Audit passes ({len(audit_events)}): avg score {avg:.2f}")
        if errors:
            summary_parts.append(f"Errors encountered: {len(errors)}")
        summary = (
            " | ".join(summary_parts) if summary_parts else "No significant events in middle range."
        )
        return {
            "summary": summary,
            "event_count": len(history),
            "truncated": len(middle) > 0,
            "header_events": header,
            "recent_events": recent,
        }


if __name__ == "__main__":
    log = SessionLog("test_sota_session")
    log.append("task.start", {"objective": "Test Managed Agents Pattern"})
    log.append("tool.call", {"tool": "ls", "args": ["D:/Hank"]})
    print(f"Wake result: {log.wake()}")
