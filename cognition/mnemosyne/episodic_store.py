import datetime
import threading

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, create_engine
from sqlalchemy.orm import sessionmaker

from src.utils.logging_config import setup_logger

try:
    from cognition.mnemosyne.base import Base
except ImportError:
    from .base import Base

logger = setup_logger(__name__)


class Episode(Base):
    __tablename__ = "episodes"
    id = Column(Integer, primary_key=True)
    session_id = Column(String(64), nullable=False)
    agent_id = Column(String(50), default="system")
    action = Column(String(255), nullable=False)
    detail = Column(Text)
    outcome = Column(String(50), default="pending")
    tokens_used = Column(Integer, default=0)
    latency_ms = Column(Float, default=0)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))


class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True)
    session_id = Column(String(64), nullable=False)
    seq_num = Column(Integer, nullable=False)
    event_type = Column(String(50), nullable=False)
    agent_id = Column(String(50), default="system")
    payload = Column(Text)  # JSON payload
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))


class EpisodicStore:
    AXIS_ID = 1

    def __init__(self, db_url: str | None = None):
        from src.utils.project_path import to_absolute_path

        db_url = db_url or f"sqlite:///{to_absolute_path('data/mnemosyne.db')}"
        self.engine = create_engine(
            db_url, connect_args={"check_same_thread": False, "timeout": 30}
        )

        from sqlalchemy import event

        @event.listens_for(self.engine, "connect")
        def _set_wal_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA synchronous=NORMAL;")
            cursor.execute("PRAGMA cache_size=-65536;")
            cursor.close()

        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

        # Phase 1.0.11: WAL Checkpoint State
        self._write_count = 0
        self._lock = threading.Lock()

    def _maybe_checkpoint(self):
        """Periodically flush WAL journal to disk (TRUNCATE mode) for Axis 1 stability."""
        with self._lock:
            self._write_count += 1
            if self._write_count >= 1000:
                try:
                    # Use raw DBAPI connection to bypass SQLAlchemy and execute checkpoint
                    with self.engine.raw_connection() as raw:
                        cursor = raw.cursor()
                        cursor.execute("PRAGMA wal_checkpoint(TRUNCATE);")
                        result = cursor.fetchone()
                        if result:
                            # result: (status, frames_checkpointed, frames_total)
                            status, frames_cp, frames_total = result
                            if status == 0:
                                logger.info(
                                    f"EpisodicStore (Axis {self.AXIS_ID}): WAL Checkpoint SUCCESS (TRUNCATE). "
                                    f"Frames: {frames_cp}/{frames_total}"
                                )
                            else:
                                logger.warning(
                                    f"EpisodicStore (Axis {self.AXIS_ID}): WAL Checkpoint BUSY/FAILED (code {status})."
                                )
                        cursor.close()
                except Exception as e:
                    logger.warning(
                        f"EpisodicStore (Axis {self.AXIS_ID}): WAL Checkpoint ERROR ({e})"
                    )
                finally:
                    # Reset counter regardless of outcome to prevent loop on failure
                    self._write_count = 0

    def log(self, session_id: str, action: str, agent_id: str = "system", **kwargs):
        session = self.Session()
        try:
            episode = Episode(session_id=session_id, agent_id=agent_id, action=action, **kwargs)
            session.add(episode)
            session.commit()
            self._maybe_checkpoint()
        except Exception as e:
            session.rollback()
            logger.error(f"EpisodicStore (Axis {self.AXIS_ID}): log failed ({e})", exc_info=True)
        finally:
            session.close()

    def recent(self, session_id: str, limit: int = 10):
        session = self.Session()
        try:
            rows = (
                session.query(Episode)
                .filter(Episode.session_id == session_id)
                .order_by(Episode.created_at.desc())
                .limit(limit)
                .all()
            )
            return [
                {
                    "action": r.action,
                    "outcome": r.outcome,
                    "detail": r.detail,
                    "timestamp": r.created_at.strftime("%H:%M %p PT")
                    if r.created_at
                    else "Unknown",
                }
                for r in rows
            ]
        except Exception as e:
            logger.error(
                f"EpisodicStore (Axis {self.AXIS_ID}): recent query failed ({e})", exc_info=True
            )
            return []
        finally:
            session.close()

    def log_event(self, session_id: str, event_type: str, payload: str, agent_id: str = "system"):
        session = self.Session()
        try:
            # Atomic sequence number increment
            from sqlalchemy import func

            last_seq = (
                session.query(func.max(Event.seq_num))
                .filter(Event.session_id == session_id)
                .scalar()
            )
            seq_num = (last_seq + 1) if last_seq is not None else 0

            event = Event(
                session_id=session_id,
                seq_num=seq_num,
                event_type=event_type,
                payload=payload,
                agent_id=agent_id,
            )
            session.add(event)
            session.commit()
            self._maybe_checkpoint()
            return seq_num
        except Exception as e:
            session.rollback()
            logger.error(f"EpisodicStore: log_event failed ({e})", exc_info=True)
            return -1
        finally:
            session.close()

    def get_events(self, session_id: str, offset: int = 0, limit: int = 100):
        session = self.Session()
        try:
            rows = (
                session.query(Event)
                .filter(Event.session_id == session_id)
                .order_by(Event.seq_num.asc())
                .offset(offset)
                .limit(limit)
                .all()
            )
            return rows
        except Exception as e:
            logger.error(f"EpisodicStore: get_events failed ({e})", exc_info=True)
            return []
        finally:
            session.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        logger.info("=== Mnemosyne Episodic Store: Firmitas Test ===")
        store = EpisodicStore()
        store.log("test_session", "test_action", "Verifying connectivity")
        recent = store.recent("test_session")
        logger.info(
            f"Connectivity verified. Recent action: {recent[0]['action'] if recent else 'None'}"
        )
    else:
        logger.info("Usage: python episodic_store.py --test (to run connectivity test)")
