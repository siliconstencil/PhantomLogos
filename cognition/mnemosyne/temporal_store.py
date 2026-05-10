"""
Mnemosyne Temporal Memory Layer (Axis 4).
SQLite time-series store for model loads, token usage, and latency tracking.
Migrated from LanceDB to SQLite for simplicity (Phase 11.14).
"""
import time
import os
import json
import sqlite3
from typing import List, Dict, Any, Optional
from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)


_initialized = False

def initialize_temporal_schema():
    """Modul seviyesinde tablo ilklendirmesi."""
    global _initialized
    if not _initialized:
        store = TemporalStore()
        store._ensure_table()
        _initialized = True

class TemporalStore:
    """
    [SRC:axis_4] Temporal memory store for time-series metrics.
    Handles record persistence, query filtering, and tiered retention summaries.
    """
    AXIS_ID = 4

    def __init__(self, db_path: Optional[str] = None):
        if not db_path:
            base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            db_path = os.path.join(base, "data", "mnemosyne.db")
        self._db_path = db_path

    def _ensure_table(self) -> None:
        """[SRC:axis_4] Ensures all temporal tables and validity schemas exist."""
        conn = sqlite3.connect(self._db_path)
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS temporal_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    session_id TEXT NOT NULL,
                    event_type TEXT,
                    event_key TEXT,
                    model_name TEXT,
                    tokens_used INTEGER DEFAULT 0,
                    latency_ms REAL DEFAULT 0.0,
                    vram_gb REAL DEFAULT 0.0,
                    metadata TEXT DEFAULT '{}',
                    valid_from REAL,
                    valid_until REAL,
                    superseded_by INTEGER
                )
            """)
            
            # Phase 11.18.13 & 11.19.1: Migration for existing tables
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(temporal_metrics)")
            columns = [info[1] for info in cursor.fetchall()]
            
            if "valid_from" not in columns:
                logger.info("TemporalStore: Adding validity columns to temporal_metrics")
                conn.execute("ALTER TABLE temporal_metrics ADD COLUMN valid_from REAL")
                conn.execute("ALTER TABLE temporal_metrics ADD COLUMN valid_until REAL")
                conn.execute("ALTER TABLE temporal_metrics ADD COLUMN superseded_by INTEGER")
                # Initialize valid_from for old records
                conn.execute("UPDATE temporal_metrics SET valid_from = timestamp WHERE valid_from IS NULL")
            
            if "event_key" not in columns:
                logger.info("TemporalStore: Adding event_key column to temporal_metrics")
                conn.execute("ALTER TABLE temporal_metrics ADD COLUMN event_key TEXT")

            # Madde 4: Summary tables
            conn.execute("""
                CREATE TABLE IF NOT EXISTS weekly_summary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT,
                    avg_latency REAL,
                    total_count INTEGER,
                    period TEXT,
                    created_at REAL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS monthly_trend (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT,
                    avg_latency REAL,
                    total_count INTEGER,
                    period TEXT,
                    created_at REAL
                )
            """)

            conn.execute("CREATE INDEX IF NOT EXISTS idx_temp_session ON temporal_metrics(session_id, timestamp DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_temp_validity ON temporal_metrics(valid_from, valid_until)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_temp_key ON temporal_metrics(event_key, valid_from DESC)")
            conn.commit()
            logger.info(f"TemporalStore (Axis {self.AXIS_ID}): SQLite tables ready.")
        except Exception as e:
            logger.error(f"TemporalStore (Axis {self.AXIS_ID}): _ensure_table failed ({e})", exc_info=True)
        finally:
            conn.close()

    def record(self, session_id: str, event_type: str, event_key: Optional[str] = None,
               model_name: str = "", tokens_used: int = 0, latency_ms: float = 0.0,
               vram_gb: float = 0.0, extra: Optional[Dict] = None,
               valid_from: Optional[float] = None, valid_until: Optional[float] = None,
               supersede: Optional[int] = None) -> int:
        """[SRC:axis_4] Records a new temporal metric with optional validity window."""
        now = time.time()
        conn = sqlite3.connect(self._db_path)
        try:
            cursor = conn.execute(
                "INSERT INTO temporal_metrics (timestamp, session_id, event_type, event_key, model_name, tokens_used, latency_ms, vram_gb, metadata, valid_from, valid_until, superseded_by) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (now, session_id, event_type, event_key, model_name, tokens_used, latency_ms, vram_gb,
                 json.dumps(extra or {"axis": "4"}), valid_from or now, valid_until, supersede)
            )
            new_id = cursor.lastrowid
            conn.commit()
            return new_id
        except Exception as e:
            logger.error(f"TemporalStore (Axis {self.AXIS_ID}): record failed for session {session_id} ({e})")
            return -1
        finally:
            conn.close()

    def supersede(self, session_id: str, event_type: str, event_key: str,
                  model_name: str = "", tokens_used: int = 0,
                  latency_ms: float = 0.0, vram_gb: float = 0.0,
                  extra: Optional[Dict] = None) -> int:
        """
        [SRC:axis_4] Atomic supersede operation:
        1. Find latest active record for event_key.
        2. Set its valid_until to now.
        3. Insert new record with valid_from = now.
        4. Update old record's superseded_by.
        """
        now = time.time()
        conn = sqlite3.connect(self._db_path)
        try:
            conn.execute("BEGIN TRANSACTION")
            # 1. Find latest
            cursor = conn.execute(
                "SELECT id FROM temporal_metrics WHERE event_key = ? AND valid_until IS NULL ORDER BY valid_from DESC LIMIT 1",
                (event_key,)
            )
            old_row = cursor.fetchone()
            
            # 2. Insert new record first to get its ID
            cursor = conn.execute(
                "INSERT INTO temporal_metrics (timestamp, session_id, event_type, event_key, model_name, tokens_used, latency_ms, vram_gb, metadata, valid_from) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (now, session_id, event_type, event_key, model_name, tokens_used, latency_ms, vram_gb,
                 json.dumps(extra or {"axis": "4"}), now)
            )
            new_id = cursor.lastrowid
            
            # 3. Update old record if exists
            if old_row:
                old_id = old_row[0]
                conn.execute(
                    "UPDATE temporal_metrics SET valid_until = ?, superseded_by = ? WHERE id = ?",
                    (now, new_id, old_id)
                )
            
            conn.commit()
            return new_id
        except Exception as e:
            conn.execute("ROLLBACK")
            logger.error(f"TemporalStore: supersede failed for {event_key} ({e})")
            return -1
        finally:
            conn.close()

    def record_with_supersede(self, session_id: str, event_type: str, event_key: str, **kwargs) -> int:
        """Convenience wrapper for supersede."""
        return self.supersede(session_id, event_type, event_key, **kwargs)

    def query(self, session_id: str, event_type: Optional[str] = None, event_key: Optional[str] = None, 
              limit: int = 50, valid_at: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        [SRC:axis_4] Queries temporal metrics with strict session isolation and optional temporal validity filter.
        """
        safe_id = "".join(c for c in session_id if c.isalnum() or c in "-_")
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        try:
            sql = "SELECT * FROM temporal_metrics WHERE session_id = ?"
            params = [safe_id]
            
            if event_type:
                sql += " AND event_type = ?"
                params.append(event_type)
            
            if event_key:
                sql += " AND event_key = ?"
                params.append(event_key)
            
            if valid_at is not None:
                sql += " AND valid_from <= ? AND (valid_until IS NULL OR valid_until > ?)"
                params.extend([valid_at, valid_at])
            
            sql += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            rows = conn.execute(sql, params).fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            logger.error(f"TemporalStore (Axis {self.AXIS_ID}): query failed for session {session_id} ({e})")
            return []
        finally:
            conn.close()

    def get_fact_history(self, event_key: str, limit: int = 20) -> List[Dict[str, Any]]:
        """[SRC:axis_4] Retrieves the lineage of a specific fact."""
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        try:
            sql = "SELECT * FROM temporal_metrics WHERE event_key = ? ORDER BY valid_from DESC LIMIT ?"
            rows = conn.execute(sql, (event_key, limit)).fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            logger.error(f"TemporalStore: get_fact_history failed for {event_key} ({e})")
            return []
        finally:
            conn.close()

    def get_fact_at(self, event_key: str, timestamp: float) -> Optional[Dict[str, Any]]:
        """[SRC:axis_4] Retrieves the specific fact version active at a given timestamp."""
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        try:
            sql = "SELECT * FROM temporal_metrics WHERE event_key = ? AND valid_from <= ? AND (valid_until IS NULL OR valid_until > ?) LIMIT 1"
            row = conn.execute(sql, (event_key, timestamp, timestamp)).fetchone()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"TemporalStore: get_fact_at failed for {event_key} at {timestamp} ({e})")
            return None
        finally:
            conn.close()

    def optimize(self) -> None:
        """SQLite VACUUM equivalent. Drops deprecated LanceDB data if present."""
        try:
            conn = sqlite3.connect(self._db_path)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA auto_vacuum=INCREMENTAL")
            conn.execute("VACUUM")
            conn.close()

            # Cleanup legacy LanceDB directory if it exists
            base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            lancedb_path = os.path.join(base, "data", "lancedb")
            if os.path.isdir(lancedb_path):
                import shutil
                shutil.rmtree(lancedb_path, ignore_errors=True)
                logger.info(f"TemporalStore: Removed legacy LanceDB directory at {lancedb_path}")

            logger.info(f"TemporalStore (Axis {self.AXIS_ID}): SQLite optimized.")
        except Exception as e:
            logger.warning(f"TemporalStore: Optimization failed ({e})")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        logger.info("=== Mnemosyne Temporal Store: Firmitas Test ===")
        store = TemporalStore()
        store.record(session_id="test_session", event_type="test", model_name="test_model", tokens_used=100, latency_ms=250.0, vram_gb=2.0)
        results = store.query(session_id="test_session", limit=5)
        logger.info(f"Connectivity verified. {len(results)} records.")
