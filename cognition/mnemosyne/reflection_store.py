import hashlib
import logging
import sqlite3
from typing import Any, cast

logger = logging.getLogger(__name__)


class ReflectionStore:
    """
    Phase 11.16: Persistence layer for Knowledge & Reflection (Axis 5, 6, 8).
    Phase 11.19: Failure Memory implementation.
    """

    def __init__(self, db_path: str | None = None):
        from src.utils.project_path import to_absolute_path

        self.db_path = db_path or to_absolute_path("data/mnemosyne.db")

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _execute(
        self, sql: str, params: tuple = (), fetch: bool = False, commit: bool = True
    ) -> int | list[dict[str, Any]]:
        """Standardized execution with explicit connection closing to prevent locks."""
        conn = self._get_conn()
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(sql, params)
            if commit:
                conn.commit()
            if fetch:
                return [dict(r) for r in cursor.fetchall()]
            return cursor.rowcount
        except Exception as e:
            if commit:
                conn.rollback()
            logger.error(f"ReflectionStore: SQL Error ({e}) | SQL: {sql[:100]}")
            raise
        finally:
            conn.close()

    def store_entities(self, session_id: str, entities: list[dict[str, Any]]):
        if not entities:
            return
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            for entity in entities:
                name, etype = entity.get("text"), entity.get("type")
                if not name or not etype:
                    continue
                sql = """
                INSERT INTO entities (name, type, session_id, frequency, last_seen)
                VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)
                ON CONFLICT(name, type) DO UPDATE SET
                    frequency = frequency + 1,
                    last_seen = CURRENT_TIMESTAMP
                """
                cursor.execute(sql, (name, etype, session_id))
            conn.commit()
        finally:
            conn.close()

    def store_relations(self, session_id: str, relations: list[dict[str, Any]]):
        if not relations:
            return
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            for rel in relations:
                sql = "INSERT INTO semantic_relations (subject, predicate, object, session_id) VALUES (?, ?, ?, ?)"
                cursor.execute(sql, (rel.get("s"), rel.get("p"), rel.get("o"), session_id))
            conn.commit()
        finally:
            conn.close()

    def store_reflection(self, session_id: str, insight: str, category: str = "general") -> bool:
        if not insight or len(insight) < 20:
            return False
        sql = "INSERT INTO reflections (insight, category, session_id) VALUES (?, ?, ?)"
        try:
            self._execute(sql, (insight, category, session_id))
            return True
        except Exception:
            return False

    def get_recent_reflections(self, limit: int = 5) -> list[dict[str, Any]]:
        sql = (
            "SELECT insight, category, created_at FROM reflections ORDER BY created_at DESC LIMIT ?"
        )
        try:
            res = self._execute(sql, (limit,), fetch=True, commit=False)
            return cast(list[dict[str, Any]], res)
        except Exception:
            return []

    def get_relevant_reflections(self, session_id: str, limit: int = 5) -> list[dict[str, Any]]:
        """[SRC:axis_8] Retrieves reflections specific to the current session."""
        sql = (
            "SELECT insight FROM reflections WHERE session_id = ? ORDER BY created_at DESC LIMIT ?"
        )
        res = self._execute(sql, (session_id, limit), fetch=True, commit=False)
        return cast(list[dict[str, Any]], res)

    def get_relevant_entities(self, keywords: list[str], limit: int = 10) -> list[dict[str, Any]]:
        """[SRC:axis_6] Retrieves entities matching keywords."""
        if not keywords:
            return []
        likes = " OR ".join(["name LIKE ?"] * len(keywords))
        params = tuple(f"%{k}%" for k in keywords) + (limit,)
        sql = f"SELECT name, type FROM entities WHERE {likes} ORDER BY frequency DESC LIMIT ?"
        res = self._execute(sql, params, fetch=True, commit=False)
        return cast(list[dict[str, Any]], res)

    def get_relevant_relations(self, entities: list[str], limit: int = 10) -> list[dict[str, Any]]:
        """[SRC:axis_5] Retrieves relations involving specified entities."""
        if not entities:
            return []
        placeholders = ",".join(["?"] * len(entities))
        sql = f"SELECT subject, predicate, object FROM semantic_relations WHERE subject IN ({placeholders}) OR object IN ({placeholders}) ORDER BY created_at DESC LIMIT ?"
        res = self._execute(
            sql, tuple(entities) + tuple(entities) + (limit,), fetch=True, commit=False
        )
        return cast(list[dict[str, Any]], res)

    def store_failure(
        self, error_type: str, root_cause: str, prevention_rule: str, severity: int = 1
    ) -> str:
        if len(prevention_rule) < 50:
            logger.warning(
                f"FailureMemory: Prevention rule too short ({len(prevention_rule)}), skipping."
            )
            return ""
        context_hash = hashlib.sha256(f"{error_type}:{root_cause[:100]}".encode()).hexdigest()[:16]
        sql = """
        INSERT INTO failure_memory (error_type, root_cause, prevention_rule, context_hash, severity, status)
        VALUES (?, ?, ?, ?, ?, 'active')
        ON CONFLICT(context_hash) DO UPDATE SET
            recurrence_count = recurrence_count + 1,
            severity = MAX(severity, excluded.severity),
            status = 'active',
            updated_at = CURRENT_TIMESTAMP
        """
        try:
            self._execute(sql, (error_type, root_cause, prevention_rule, context_hash, severity))
            return context_hash
        except Exception as e:
            logger.error(f"ReflectionStore: store_failure failed: {e}")
            raise

    def get_prevention_rules(self, limit: int = 5) -> list[dict[str, Any]]:
        sql = """
        SELECT error_type, prevention_rule, recurrence_count, severity
        FROM failure_memory WHERE status = 'active'
        ORDER BY severity DESC, recurrence_count DESC LIMIT ?
        """
        try:
            res = self._execute(sql, (limit,), fetch=True, commit=False)
            return cast(list[dict[str, Any]], res)
        except Exception:
            return []

    def resolve_failure(self, context_hash: str):
        sql = "UPDATE failure_memory SET status = 'archived', updated_at = CURRENT_TIMESTAMP WHERE context_hash = ?"
        self._execute(sql, (context_hash,))
