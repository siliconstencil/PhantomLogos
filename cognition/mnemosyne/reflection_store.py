import sqlite3
import logging
from typing import List, Dict, Any, Optional
import datetime
import hashlib

logger = logging.getLogger(__name__)

class ReflectionStore:
    """
    Phase 11.16: Persistence layer for Knowledge & Reflection (Axis 5, 6, 8).
    Phase 11.19: Failure Memory implementation.
    """
    
    def __init__(self, db_path: str = "data/mnemosyne.db"):
        self.db_path = db_path
        
    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _execute(self, sql: str, params: tuple = (), fetch: bool = False, commit: bool = True):
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
            if commit: conn.rollback()
            logger.error(f"ReflectionStore: SQL Error ({e}) | SQL: {sql[:100]}")
            raise
        finally:
            conn.close()

    def store_entities(self, session_id: str, entities: List[Dict[str, Any]]):
        if not entities: return
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            for entity in entities:
                name, etype = entity.get("text"), entity.get("type")
                if not name or not etype: continue
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

    def store_relations(self, session_id: str, relations: List[Dict[str, Any]]):
        if not relations: return
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
        if not insight or len(insight) < 20: return False
        sql = "INSERT INTO reflections (insight, category, session_id) VALUES (?, ?, ?)"
        try:
            self._execute(sql, (insight, category, session_id))
            return True
        except Exception: return False

    def get_recent_reflections(self, limit: int = 5) -> List[Dict[str, Any]]:
        sql = "SELECT insight, category, created_at FROM reflections ORDER BY created_at DESC LIMIT ?"
        try:
            return self._execute(sql, (limit,), fetch=True, commit=False)
        except Exception: return []

    def store_failure(self, error_type: str, root_cause: str, prevention_rule: str, severity: int = 1) -> str:
        if len(prevention_rule) < 50:
            logger.warning(f"FailureMemory: Prevention rule too short ({len(prevention_rule)}), skipping.")
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

    def get_prevention_rules(self, limit: int = 5) -> List[Dict[str, Any]]:
        sql = """
        SELECT error_type, prevention_rule, recurrence_count, severity 
        FROM failure_memory WHERE status = 'active' 
        ORDER BY severity DESC, recurrence_count DESC LIMIT ?
        """
        try:
            return self._execute(sql, (limit,), fetch=True, commit=False)
        except Exception: return []

    def resolve_failure(self, context_hash: str):
        sql = "UPDATE failure_memory SET status = 'archived', updated_at = CURRENT_TIMESTAMP WHERE context_hash = ?"
        self._execute(sql, (context_hash,))
