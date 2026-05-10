import logging
import sqlite3
import warnings

# Phase 11.21: Suppress GenAI deprecation warnings (L0 mandate)
warnings.filterwarnings("ignore", category=FutureWarning, module="google.generativeai")

class SQLiteHandler(logging.Handler):
    """
    Custom logging handler to write logs into SQLite database (Axis 7: Operational).
    Uses persistent connection with WAL mode for performance.
    """
    def __init__(self, db_path: str):
        super().__init__()
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._ensure_table()

    def _ensure_table(self):
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS operational_logs_v2 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                session_id TEXT DEFAULT 'default',
                agent_id TEXT DEFAULT 'system',
                tool_name TEXT,
                name TEXT,
                level TEXT,
                message TEXT
            )
        """)
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_agent_timestamp ON operational_logs_v2 (agent_id, timestamp)
        """)
        self._conn.commit()

    def emit(self, record):
        log_entry = self.format(record)
        agent = getattr(record, 'agent_id', 'system')
        tool = getattr(record, 'tool_name', None)
        session = getattr(record, 'session_id', 'default')
        try:
            self._conn.execute(
                "INSERT INTO operational_logs_v2 (session_id, agent_id, tool_name, name, level, message) VALUES (?, ?, ?, ?, ?, ?)",
                (session, agent, tool, record.name, record.levelname, log_entry))
            self._conn.commit()
        except Exception:
            self.handleError(record)

    def close(self):
        """Cleanly close the database connection."""
        try:
            if hasattr(self, "_conn") and self._conn:
                self._conn.close()
        except Exception as e:
            print(f"SQLiteHandler close error: {e}")
        super().close()

def setup_logger(name: str) -> logging.Logger:
    """
    Sets up a standard logger with console and SQLite handlers only.
    No file-based logging -- all persistence is database-first.
    """
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Console Handler (stdout only)
        c_handler = logging.StreamHandler()
        c_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        c_handler.setFormatter(c_format)
        logger.addHandler(c_handler)

        # SQLite Handler (Axis 7 Operational Store)
        try:
            import os
            base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            db_path = os.path.join(base, "data", "mnemosyne.db")
            s_handler = SQLiteHandler(db_path)
            s_handler.setFormatter(c_format)
            logger.addHandler(s_handler)
        except Exception as e:
            print(f"Failed to initialize SQLiteHandler: {e}")
        
    return logger
