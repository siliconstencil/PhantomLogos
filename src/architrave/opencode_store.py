"""
OpenCode External Store (Axis 13).
Read-only bridge to D:/opencode/opencode.db for cross-session context.
"""

import os
import sqlite3
from typing import Any

from src.utils.logging_config import setup_logger
from src.utils.project_path import get_project_root

logger = setup_logger(__name__)


class OpenCodeStore:
    AXIS_ID = 13

    def __init__(self, db_path: str | None = None) -> None:
        if not db_path:
            opencode_home = os.getenv(
                "OPENCODE_CONFIG_DIR", os.path.join(get_project_root(), "opencode")
            )
            db_path = os.path.join(opencode_home, "opencode.db")
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection | None:
        if not os.path.isfile(self.db_path):
            return None
        return sqlite3.connect(self.db_path)

    def list_sessions(self, limit: int = 10) -> list[dict[str, Any]]:
        conn = self._connect()
        if not conn:
            logger.debug(f"OpenCodeStore: DB not found at {self.db_path}")
            return []
        try:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT s.id, s.title, s.agent, s.model, s.version, s.time_created, "
                "COUNT(m.id) as msg_count "
                "FROM session s LEFT JOIN message m ON m.session_id = s.id "
                "WHERE s.project_id = ? "
                "GROUP BY s.id ORDER BY s.time_created DESC LIMIT ?",
                ("global", limit),
            ).fetchall()
            return [
                {
                    "session_id": r["id"],
                    "title": r["title"],
                    "agent": r["agent"],
                    "model": r["model"],
                    "version": r["version"],
                    "messages": r["msg_count"],
                }
                for r in rows
            ]
        except Exception as e:
            logger.warning(f"OpenCodeStore (Axis {self.AXIS_ID}): list_sessions failed ({e})")
            return []
        finally:
            conn.close()

    def get_session_messages(self, session_id: str, limit: int = 50) -> list[dict[str, Any]]:
        conn = self._connect()
        if not conn:
            return []
        try:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT id, time_created, data FROM message "
                "WHERE session_id = ? ORDER BY time_created ASC LIMIT ?",
                (session_id, limit),
            ).fetchall()
            return [
                {"id": r["id"], "time_created": r["time_created"], "data": r["data"]} for r in rows
            ]
        except Exception as e:
            logger.warning(
                f"OpenCodeStore (Axis {self.AXIS_ID}): get_session_messages failed ({e})"
            )
            return []
        finally:
            conn.close()

    def get_cross_session_patterns(self) -> dict[str, Any]:
        conn = self._connect()
        if not conn:
            return {"sessions": 0, "top_agents": [], "top_models": []}
        try:
            curs = conn.cursor()
            total = curs.execute("SELECT COUNT(*) FROM session").fetchone()[0]
            agents = curs.execute(
                "SELECT agent, COUNT(*) as cnt FROM session WHERE agent NOT NULL "
                "GROUP BY agent ORDER BY cnt DESC LIMIT 5"
            ).fetchall()
            models = curs.execute(
                "SELECT model, COUNT(*) as cnt FROM session WHERE model NOT NULL "
                "GROUP BY model ORDER BY cnt DESC LIMIT 5"
            ).fetchall()
            avg_msgs = (
                curs.execute(
                    "SELECT AVG(cnt) FROM (SELECT COUNT(*) as cnt FROM message GROUP BY session_id)"
                ).fetchone()[0]
                or 0
            )
            return {
                "sessions": total,
                "top_agents": [{"agent": r[0], "count": r[1]} for r in agents],
                "top_models": [{"model": r[0], "count": r[1]} for r in models],
                "avg_messages_per_session": round(avg_msgs, 1),
            }
        except Exception as e:
            logger.warning(
                f"OpenCodeStore (Axis {self.AXIS_ID}): get_cross_session_patterns failed ({e})"
            )
            return {
                "sessions": 0,
                "top_agents": [],
                "top_models": [],
                "avg_messages_per_session": 0,
            }
        finally:
            conn.close()


if __name__ == "__main__":
    store = OpenCodeStore()
    sessions = store.list_sessions(3)
    patterns = store.get_cross_session_patterns()
    logger.info(f"OpenCodeStore (Axis 13) Firmitas: {patterns.get('sessions')} sessions")
    if sessions:
        first = sessions[0]
        msgs = store.get_session_messages(first["session_id"], 2)
        logger.info(f"  Latest: {first['title']} ({first['agent']}) - {len(msgs)} messages sampled")
