import json
import logging
import os
import sqlite3
from datetime import UTC, datetime
from logging.handlers import RotatingFileHandler


class SessionFilter(logging.Filter):
    """
    Ensures session_id and agent_id are always present in the log record.
    Defaults to 'unknown' if not provided by the caller.
    """

    def filter(self, record) -> bool:
        if not hasattr(record, "session_id") or record.session_id == "unknown":
            record.session_id = os.getenv("SESSION_ID", "unknown")
        if not hasattr(record, "agent_id") or record.agent_id == "unknown":
            record.agent_id = os.getenv("LOG_AGENT_ID", "unknown")
        return True


# Global LogRecordFactory to automatically populate agent_id and session_id
_old_factory = logging.getLogRecordFactory()


def _custom_record_factory(*args, **kwargs):
    record = _old_factory(*args, **kwargs)
    if not hasattr(record, "session_id") or record.session_id == "unknown":
        record.session_id = os.getenv("SESSION_ID", "unknown")
    if not hasattr(record, "agent_id") or record.agent_id == "unknown":
        record.agent_id = os.getenv("LOG_AGENT_ID", "unknown")
    return record


logging.setLogRecordFactory(_custom_record_factory)


class JSONFormatter(logging.Formatter):
    """
    Formats log records as JSON Lines (JSONL).
    Includes system metadata, session/agent IDs, and extra fields.
    """

    def format(self, record):
        log_obj = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "module": record.module,
            "name": record.name,
            "session_id": getattr(record, "session_id", "unknown"),
            "agent_id": getattr(record, "agent_id", "unknown"),
            "message": record.getMessage(),
        }

        # Handle exceptions if present
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        # Include extra fields (anything in record.__dict__ that isn't standard)
        standard_fields = {
            "args",
            "asctime",
            "created",
            "exc_info",
            "exc_text",
            "filename",
            "funcName",
            "levelname",
            "levelno",
            "lineno",
            "module",
            "msecs",
            "msg",
            "name",
            "pathname",
            "process",
            "processName",
            "relativeCreated",
            "stack_info",
            "thread",
            "threadName",
            "session_id",
            "agent_id",
            "message",
            "taskName",
        }
        extra = {k: v for k, v in record.__dict__.items() if k not in standard_fields}
        if extra:
            log_obj["extra"] = extra
        else:
            log_obj["extra"] = {}

        return json.dumps(log_obj, ensure_ascii=False)


class SQLiteHandler(logging.Handler):
    """
    [DEPRECATED - K2.8 Remediation]
    Custom logging handler to write logs into SQLite database (Axis 7: Operational).
    Uses persistent connection with WAL mode for performance.
    """

    def __init__(self, db_path: str) -> None:
        super().__init__()
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._ensure_table()

    def _ensure_table(self) -> None:
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

    def emit(self, record) -> None:
        log_entry = self.format(record)
        agent = getattr(record, "agent_id", "system")
        tool = getattr(record, "tool_name", None)
        session = getattr(record, "session_id", "default")
        try:
            self._conn.execute(
                "INSERT INTO operational_logs_v2 (session_id, agent_id, tool_name, name, level, message) VALUES (?, ?, ?, ?, ?, ?)",
                (session, agent, tool, record.name, record.levelname, log_entry),
            )
            self._conn.commit()
        except Exception:
            self.handleError(record)

    def close(self) -> None:
        """Cleanly close the database connection."""
        try:
            if hasattr(self, "_conn") and self._conn:
                self._conn.close()
        except Exception as e:
            print(f"SQLiteHandler close error: {e}")
        super().close()


def setup_logger(name: str, agent_id: str | None = None) -> logging.Logger:
    """
    Sets up a dual-stream logger (Text + JSONL).
    Includes SessionFilter for metadata persistence.
    """
    if agent_id:
        os.environ["LOG_AGENT_ID"] = agent_id

    logger = logging.getLogger(name)

    # Apply SessionFilter idempotently
    if not any(isinstance(f, SessionFilter) for f in logger.filters):
        logger.addFilter(SessionFilter())

    if not logger.handlers:
        # Dynamic Log Level from Environment (Default: INFO)
        log_level_name = os.getenv("LOG_LEVEL", "INFO").upper()
        log_level = getattr(logging, log_level_name, logging.INFO)
        logger.setLevel(log_level)

        # Standard Text Format
        c_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        # Console Handler (stdout)
        c_handler = logging.StreamHandler()
        c_handler.setFormatter(c_format)
        logger.addHandler(c_handler)

        # Log Directory Setup
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        log_dir = os.path.join(base, "logs")
        os.makedirs(log_dir, exist_ok=True)

        # 1. Rotating File Handler (Text - system.log)
        try:
            log_file = os.path.join(log_dir, "system.log")
            # Upgrade: 10MB / 5 backups
            f_handler = RotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024, backupCount=5)
            f_handler.setFormatter(c_format)
            logger.addHandler(f_handler)
        except Exception as e:
            print(f"Failed to initialize RotatingFileHandler (Text): {e}")

        # 2. Rotating File Handler (JSONL - system.json)
        try:
            json_file = os.path.join(log_dir, "system.json")
            # Upgrade: 10MB / 5 backups
            j_handler = RotatingFileHandler(json_file, maxBytes=10 * 1024 * 1024, backupCount=5)
            j_handler.setFormatter(JSONFormatter())
            logger.addHandler(j_handler)
        except Exception as e:
            print(f"Failed to initialize RotatingFileHandler (JSON): {e}")

    return logger


def setup_logging(log_dir=None, level=logging.INFO, agent_id="system") -> logging.Logger:
    """Legacy/Validation wrapper to configure logging and return a logger."""
    return setup_logger(__name__, agent_id=agent_id)


def get_json_logger(name: str) -> logging.Logger:
    """Convenience helper to retrieve configured logger."""
    return setup_logger(name)


def log_system_event(level: str, message: str, extra: dict | None = None) -> None:
    """
    Directly writes system-level events to the SQLite operational_logs_v2 table.
    Bypasses the standard logger chain for integrity and infrastructure events.
    """
    from .project_path import get_project_root

    db_path = os.path.join(get_project_root(), "data/mnemosyne.db")
    try:
        handler = SQLiteHandler(db_path)
        # Create a LogRecord manually
        level_no = getattr(logging, level.upper(), logging.INFO)
        record = logging.LogRecord(
            name="system.event",
            level=level_no,
            pathname="internal",
            lineno=0,
            msg=message,
            args=(),
            exc_info=None,
        )
        # Map fields to match record expectations in SQLiteHandler
        record.levelname = level.upper()
        record.session_id = "system"
        record.agent_id = "SovereignEngine"
        if extra:
            for k, v in extra.items():
                setattr(record, k, v)

        handler.emit(record)
        handler.close()
    except Exception as e:
        # Fallback to console if DB write fails
        print(f"FAILED to log_system_event: {message} (Error: {e})")
