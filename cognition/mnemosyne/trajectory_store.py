import datetime
import threading

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    event,
)
from sqlalchemy.orm import sessionmaker

from cognition.mnemosyne.models import MnemosyneBase
from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)


class TrajectorySession(MnemosyneBase):
    __tablename__ = "trajectory_sessions"
    id = Column(Integer, primary_key=True)
    session_id = Column(String(64), nullable=False, index=True)
    task = Column(Text)
    total_steps = Column(Integer, default=0)
    cumulative_reward = Column(Float, default=0.0)
    final_score = Column(Float)
    total_tokens = Column(Integer, default=0)
    total_latency_ms = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))
    completed_at = Column(DateTime)


class TrajectoryStep(MnemosyneBase):
    __tablename__ = "trajectory_steps"
    id = Column(Integer, primary_key=True)
    session_id = Column(String(64), nullable=False, index=True)
    trajectory_id = Column(Integer, ForeignKey("trajectory_sessions.id"))
    step_index = Column(Integer, nullable=False)
    node_name = Column(String(100), nullable=False)
    reward = Column(Float, default=0.0)
    score = Column(Float)
    tokens_used = Column(Integer, default=0)
    latency_ms = Column(Float, default=0.0)
    tier = Column(Integer)
    model_tier = Column(String(50))
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))


class TrajectoryStore:
    AXIS_ID = 1

    def __init__(self, db_url: str | None = None):
        from src.utils.project_path import to_absolute_path

        db_url = db_url or f"sqlite:///{to_absolute_path('data/mnemosyne.db')}"
        self.engine = create_engine(
            db_url, connect_args={"check_same_thread": False, "timeout": 30}
        )

        @event.listens_for(self.engine, "connect")
        def _set_wal_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA synchronous=NORMAL;")
            cursor.execute("PRAGMA cache_size=-65536;")
            cursor.close()

        MnemosyneBase.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self._lock = threading.Lock()

    def create_session(self, session_id: str, task: str) -> int:
        with self._lock:
            sess = self.Session()
            try:
                record = TrajectorySession(session_id=session_id, task=task[:2000])
                sess.add(record)
                sess.commit()
                logger.info(
                    f"trajectory_store: Created trajectory session {record.id} for {session_id}"
                )
                return record.id
            except Exception as e:
                sess.rollback()
                logger.error(f"trajectory_store: create_session failed ({e})")
                return 0
            finally:
                sess.close()

    def record_step(
        self,
        session_id: str,
        trajectory_id: int,
        step_index: int,
        node_name: str,
        score: float | None = None,
        tokens_used: int = 0,
        latency_ms: float = 0.0,
        tier: int = 2,
        model_tier: str = "",
    ) -> int:
        with self._lock:
            sess = self.Session()
            try:
                reward = 0.0
                if score is not None:
                    clamped_score = max(0.0, min(1.0, score))
                    reward = (clamped_score - 0.5) * 2.0
                step = TrajectoryStep(
                    session_id=session_id,
                    trajectory_id=trajectory_id,
                    step_index=step_index,
                    node_name=node_name,
                    reward=reward,
                    score=score,
                    tokens_used=tokens_used,
                    latency_ms=latency_ms,
                    tier=tier,
                    model_tier=model_tier,
                )
                sess.add(step)
                traj = sess.query(TrajectorySession).filter_by(id=trajectory_id).first()
                if traj:
                    traj.total_steps = step_index
                    traj.cumulative_reward += reward
                    traj.total_tokens += tokens_used
                    traj.total_latency_ms += latency_ms
                sess.commit()
                return step.id
            except Exception as e:
                sess.rollback()
                logger.error(f"trajectory_store: record_step failed ({e})")
                return 0
            finally:
                sess.close()

    def finalize_session(self, trajectory_id: int, score: float):
        with self._lock:
            sess = self.Session()
            try:
                traj = sess.query(TrajectorySession).filter_by(id=trajectory_id).first()
                if traj:
                    traj.final_score = score
                    traj.completed_at = datetime.datetime.now(datetime.UTC)
                sess.commit()
            except Exception as e:
                sess.rollback()
                logger.error(f"trajectory_store: finalize_session failed ({e})")
            finally:
                sess.close()

    def get_trajectory(self, trajectory_id: int) -> dict | None:
        with self._lock:
            sess = self.Session()
            try:
                traj = sess.query(TrajectorySession).filter_by(id=trajectory_id).first()
                if not traj:
                    return None
                steps = (
                    sess.query(TrajectoryStep)
                    .filter_by(trajectory_id=trajectory_id)
                    .order_by(TrajectoryStep.step_index)
                    .all()
                )
                return {
                    "id": traj.id,
                    "session_id": traj.session_id,
                    "task": traj.task,
                    "total_steps": traj.total_steps,
                    "cumulative_reward": traj.cumulative_reward,
                    "final_score": traj.final_score,
                    "total_tokens": traj.total_tokens,
                    "total_latency_ms": traj.total_latency_ms,
                    "steps": [
                        {
                            "step_index": s.step_index,
                            "node_name": s.node_name,
                            "reward": s.reward,
                            "score": s.score,
                            "tokens_used": s.tokens_used,
                            "latency_ms": s.latency_ms,
                            "tier": s.tier,
                            "model_tier": s.model_tier,
                        }
                        for s in steps
                    ],
                }
            except Exception as e:
                logger.error(f"trajectory_store: get_trajectory failed ({e})")
                return None
            finally:
                sess.close()
