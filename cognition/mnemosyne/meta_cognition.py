import datetime
import json
from typing import Any, Dict, List, Optional
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float
from sqlalchemy.orm import sessionmaker, declarative_base
from src.utils.logging_config import setup_logger
try:
    from .base import Base
    from .temporal_store import TemporalStore
except ImportError:
    from base import Base
    from temporal_store import TemporalStore

logger = setup_logger(__name__)

ReliabilityBase = declarative_base()


class MetaRecord(Base):
    __tablename__ = "meta_cognition"
    id = Column(Integer, primary_key=True)
    agent_id = Column(String(50), default="system")
    session_id = Column(String(100), default="")
    task = Column(Text)
    draft_quality = Column(Float, default=0.5)
    critique_severity = Column(Float, default=0.5)
    refinement_improvement = Column(Float, default=0)
    num_iterations = Column(Integer, default=1)
    pattern_notes = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))


class AgentReliability(ReliabilityBase):
    __tablename__ = "agent_reliability"
    id = Column(Integer, primary_key=True)
    agent_id = Column(String(50), nullable=False, unique=True)
    reliability_score = Column(Float, default=1.0)
    total_violations = Column(Integer, default=0)
    last_violation_type = Column(String(50))
    last_violation_at = Column(DateTime)
    updated_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))


class AgentExperience(Base):
    __tablename__ = "agent_experience"
    id = Column(Integer, primary_key=True)
    agent_id = Column(String(50), nullable=False)
    session_id = Column(String(64), default="")
    task_pattern = Column(String(100), default="general")
    total_tasks = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    avg_quality = Column(Float, default=0.5)
    best_model = Column(String(100), default="")
    best_temperature = Column(Float, default=0.3)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))


RELIABILITY_THRESHOLD_LOCK = 0.3


class MetaCognitionStore:
    AXIS_ID = 8

    def __init__(self, db_url: str = "sqlite:///data/mnemosyne.db", reliability_db: str = "sqlite:///data/reliability.db"):
        self.engine = create_engine(db_url, connect_args={"check_same_thread": False})
        Base.metadata.create_all(self.engine)
        self._reliability_engine = create_engine(reliability_db, connect_args={"check_same_thread": False})
        ReliabilityBase.metadata.create_all(self._reliability_engine)
        self.Session = sessionmaker(bind=self.engine)

    def record(self, task: str = "", draft_quality: float = 0.5, critique_severity: float = 0.5,
               improvement: float = 0, iterations: int = 1, agent_id: str = "system", 
               session_id: str = "", score: float = None, flaws: list = None):
        session = self.Session()
        try:
            # Phase 4 override: if score/flaws provided, use them
            q = score if score is not None else draft_quality
            notes = json.dumps(flaws) if flaws else None
            
            record = MetaRecord(
                task=task[:500], draft_quality=q,
                critique_severity=critique_severity, refinement_improvement=improvement,
                num_iterations=iterations, agent_id=agent_id, session_id=session_id,
                pattern_notes=notes
            )
            session.add(record)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"MetaCognitionStore (Axis {self.AXIS_ID}): record failed ({e})", exc_info=True)
        finally:
            session.close()

    def patterns(self, limit: int = 5):
        session = self.Session()
        try:
            rows = session.query(MetaRecord).order_by(MetaRecord.draft_quality.asc()).limit(limit).all()
            return [
                {"task": r.task[:80], "draft": r.draft_quality, "improvement": r.refinement_improvement}
                for r in rows
            ]
        except Exception as e:
            logger.error(f"MetaCognitionStore (Axis {self.AXIS_ID}): patterns failed ({e})", exc_info=True)
            return []
        finally:
            session.close()

    def record_experience(self, agent_id: str, session_id: str = "", task_pattern: str = "general",
                           success: bool = True, quality: float = 0.5,
                           model_used: str = "", temperature: float = 0.3):
        """Record an agent's task experience for performance tracking."""
        session = self.Session()
        try:
            record = session.query(AgentExperience).filter(
                AgentExperience.agent_id == agent_id,
                AgentExperience.task_pattern == task_pattern
            ).first()
            if record:
                record.total_tasks += 1
                if success:
                    record.success_count += 1
                else:
                    record.failure_count += 1
                record.avg_quality = (record.avg_quality * (record.total_tasks - 1) + quality) / record.total_tasks
                # Sprint B: Improve best_model selection
                if model_used and (quality >= record.avg_quality or not record.best_model):
                    record.best_model = model_used
                    record.best_temperature = temperature
                record.updated_at = datetime.datetime.now(datetime.timezone.utc)
            else:
                record = AgentExperience(
                    agent_id=agent_id, session_id=session_id, task_pattern=task_pattern,
                    total_tasks=1, success_count=1 if success else 0, failure_count=0 if success else 1,
                    avg_quality=quality, best_model=model_used, best_temperature=temperature,
                )
                session.add(record)
            session.commit()
            logger.info(f"MetaCognition: Experience recorded for {agent_id}/{task_pattern} (q={quality:.2f}, ok={success})")
        except Exception as e:
            session.rollback()
            logger.error(f"MetaCognitionStore: record_experience failed ({e})", exc_info=True)
        finally:
            session.close()

    def get_experience(self, agent_id: str) -> list:
        """Get all experience records for an agent."""
        session = self.Session()
        try:
            records = session.query(AgentExperience).filter(
                AgentExperience.agent_id == agent_id
            ).order_by(AgentExperience.success_count.desc()).all()
            return [{
                "agent_id": r.agent_id, "task_pattern": r.task_pattern,
                "total_tasks": r.total_tasks, "failure_count": r.failure_count,
                "success_rate": round(r.success_count / max(r.total_tasks, 1), 2),
                "avg_quality": round(r.avg_quality, 2), "best_model": r.best_model,
                "best_temperature": r.best_temperature
            } for r in records]
        except Exception as e:
            logger.error(f"MetaCognitionStore: get_experience failed ({e})", exc_info=True)
            return []
        finally:
            session.close()

    def get_reliability(self, agent_id: str = "system") -> float:
        """Get current reliability score for an agent. Returns 0.0-1.0."""
        ReliabilitySession = sessionmaker(bind=self._reliability_engine)
        session = ReliabilitySession()
        try:
            entry = session.query(AgentReliability).filter(
                AgentReliability.agent_id == agent_id
            ).first()
            return entry.reliability_score if entry else 1.0
        except Exception as e:
            logger.error(f"MetaCognitionStore: get_reliability failed ({e})")
            return 1.0
        finally:
            session.close()

    # Phase 11.18.4: Session-level shadow violation counter
    _shadow_violation_counts = {} # {session_id: count}

    def record_inconsistency(self, agent_id: str, session_id: str, claim: str, reasoning_val: Any, reality_val: Any):
        """Phase 11.18.4: Records technical mismatches for Axis 11 auditing."""
        session = self.Session()
        try:
            # We use pattern_notes in MetaRecord to store the delta for now
            note = {
                "type": "inconsistency_evidence",
                "claim": claim,
                "reasoning": reasoning_val,
                "reality": reality_val,
                "axis": 11
            }
            record = MetaRecord(
                agent_id=agent_id,
                session_id=session_id,
                task=f"Inconsistency: {claim}",
                pattern_notes=json.dumps(note),
                draft_quality=0.0 # Force zero quality for lying
            )
            session.add(record)
            session.commit()
            logger.info(f"MetaCognition: Inconsistency evidence recorded for {claim} (Axis 11)")
        except Exception as e:
            session.rollback()
            logger.error(f"MetaCognitionStore: Failed to record inconsistency ({e})")
        finally:
            session.close()

    def adjust_reliability(self, agent_id: str, delta: float, violation_type: str = "", session_id: str = "default"):
        """Adjust agent reliability score. Delta can be negative (penalty) or positive (reward)."""
        ReliabilitySession = sessionmaker(bind=self._reliability_engine)
        session = ReliabilitySession()
        try:
            entry = session.query(AgentReliability).filter(
                AgentReliability.agent_id == agent_id
            ).first()
            if not entry:
                entry = AgentReliability(agent_id=agent_id, reliability_score=1.0)
                session.add(entry)
            
            entry.reliability_score = max(0.0, min(1.0, entry.reliability_score + delta))
            if delta < 0:
                entry.total_violations = (entry.total_violations or 0) + 1
                entry.last_violation_type = violation_type
                entry.last_violation_at = datetime.datetime.now(datetime.timezone.utc)
            
            entry.updated_at = datetime.datetime.now(datetime.timezone.utc)
            session.commit()
            
            logger.info(
                f"MetaCognition: {agent_id} reliability -> {entry.reliability_score:.2f} "
                f"(delta={delta:+.2f}, violation={violation_type}, session={session_id})"
            )
            
            # [SRC:axis_4] Record truth update in Temporal Graph
            try:
                TemporalStore().record_with_supersede(
                    session_id=session_id,
                    event_type="reliability_update",
                    event_key=f"reliability.{agent_id}",
                    extra={"delta": delta, "score": entry.reliability_score, "violation": violation_type}
                )
            except Exception as te:
                logger.warning(f"MetaCognition: Failed to record temporal fact for {agent_id} ({te})")
            
            # S4.1: Trigger Auto-Rotation after 2 consecutive shadow verification failures
            if "shadow_verification_failed" in violation_type:
                count = self._shadow_violation_counts.get(session_id, 0) + 1
                self._shadow_violation_counts[session_id] = count
                if count >= 2:
                    logger.error(f"MetaCognition: {count} consecutive shadow failures in {session_id}. TRIGGERING ROTATION.")
                    try:
                        from src.lachesis.self_tuner import SelfTuner
                        SelfTuner().apply_rotation(session_id, agent_id, reason=violation_type)
                        # Reset counter after rotation
                        self._shadow_violation_counts[session_id] = 0
                    except Exception as re:
                        logger.warning(f"MetaCognition: Rotation trigger failed ({re})")

            if entry.reliability_score <= RELIABILITY_THRESHOLD_LOCK:
                logger.warning(
                    f"MetaCognition: {agent_id} reliability below threshold "
                    f"({RELIABILITY_THRESHOLD_LOCK}). L0 approval required for all actions."
                )
        except Exception as e:
            session.rollback()
            logger.error(f"MetaCognitionStore: adjust_reliability failed ({e})", exc_info=True)
        finally:
            session.close()


if __name__ == "__main__":
    logger.info("=== Meta-Cognition Store (Axis 8): Firmitas Test ===")
    store = MetaCognitionStore()
    store.record("test_task", 0.8, 0.2)
    pats = store.patterns()
    logger.info(f"Pattern count: {len(pats)}")
    
    store.adjust_reliability("sophia", -0.2, "emoji_ban")
    score = store.get_reliability("sophia")
    logger.info(f"Sophia reliability: {score:.2f}")
