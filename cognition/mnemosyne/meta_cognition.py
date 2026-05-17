import datetime
import json
from typing import Any

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from src.utils.logging_config import setup_logger

try:
    from .base import Base
    from .temporal_store import TemporalStore
except ImportError:
    from base import Base
    from temporal_store import TemporalStore

logger = setup_logger(__name__)

from .models import MnemosyneBase, ReliabilityBase, MetaRecord, AgentReliability, AgentExperience

RELIABILITY_THRESHOLD_LOCK = 0.3
_RELIABILITY_CACHE = {}  # [SRC:axis_8] Process-level cache for reliability fallback


class MetaCognitionStore:
    AXIS_ID = 8

    def __init__(self, db_url: str | None = None, reliability_db: str | None = None):
        from src.utils.project_path import to_absolute_path

        db_url = db_url or f"sqlite:///{to_absolute_path('data/mnemosyne.db')}"
        reliability_db = reliability_db or f"sqlite:///{to_absolute_path('data/reliability.db')}"
        self.engine = create_engine(
            db_url, connect_args={"check_same_thread": False, "timeout": 30}
        )
        try:
            MnemosyneBase.metadata.create_all(self.engine)
        except Exception as e:
            logger.warning(f"MetaCognitionStore: Primary DB init failed ({e})")

        self._reliability_engine = create_engine(
            reliability_db, connect_args={"check_same_thread": False}
        )
        try:
            ReliabilityBase.metadata.create_all(self._reliability_engine)
        except Exception as e:
            logger.warning(f"MetaCognitionStore: Reliability DB init failed ({e})")

        self.Session = sessionmaker(bind=self.engine)

    def record(
        self,
        task: str = "",
        draft_quality: float = 0.5,
        critique_severity: float = 0.5,
        improvement: float = 0,
        iterations: int = 1,
        agent_id: str = "system",
        session_id: str = "",
        score: float = None,
        flaws: list = None,
    ):
        session = self.Session()
        try:
            # Phase 4 override: if score/flaws provided, use them
            q = score if score is not None else draft_quality
            notes = json.dumps(flaws) if flaws else None

            record = MetaRecord(
                task=task[:500],
                draft_quality=q,
                critique_severity=critique_severity,
                refinement_improvement=improvement,
                num_iterations=iterations,
                agent_id=agent_id,
                session_id=session_id,
                pattern_notes=notes,
            )
            session.add(record)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(
                f"MetaCognitionStore (Axis {self.AXIS_ID}): record failed ({e})", exc_info=True
            )
        finally:
            session.close()

    def patterns(self, limit: int = 5):
        session = self.Session()
        try:
            rows = (
                session.query(MetaRecord)
                .order_by(MetaRecord.draft_quality.asc())
                .limit(limit)
                .all()
            )
            return [
                {
                    "task": r.task[:80],
                    "draft": r.draft_quality,
                    "improvement": r.refinement_improvement,
                }
                for r in rows
            ]
        except Exception as e:
            logger.error(
                f"MetaCognitionStore (Axis {self.AXIS_ID}): patterns failed ({e})", exc_info=True
            )
            return []
        finally:
            session.close()

    def record_experience(
        self,
        agent_id: str,
        session_id: str = "",
        task_pattern: str = "general",
        success: bool = True,
        quality: float = 0.5,
        model_used: str = "",
        temperature: float = 0.3,
    ):
        """Record an agent's task experience for performance tracking."""
        session = self.Session()
        try:
            record = (
                session.query(AgentExperience)
                .filter(
                    AgentExperience.agent_id == agent_id,
                    AgentExperience.task_pattern == task_pattern,
                )
                .first()
            )
            if record:
                record.total_tasks += 1
                if success:
                    record.success_count += 1
                else:
                    record.failure_count += 1
                record.avg_quality = (
                    record.avg_quality * (record.total_tasks - 1) + quality
                ) / record.total_tasks
                # Sprint B: Improve best_model selection
                if model_used and (quality >= record.avg_quality or not record.best_model):
                    record.best_model = model_used
                    record.best_temperature = temperature
                record.updated_at = datetime.datetime.now(datetime.UTC)
            else:
                record = AgentExperience(
                    agent_id=agent_id,
                    session_id=session_id,
                    task_pattern=task_pattern,
                    total_tasks=1,
                    success_count=1 if success else 0,
                    failure_count=0 if success else 1,
                    avg_quality=quality,
                    best_model=model_used,
                    best_temperature=temperature,
                )
                session.add(record)
            session.commit()
            logger.info(
                f"MetaCognition: Experience recorded for {agent_id}/{task_pattern} (q={quality:.2f}, ok={success})"
            )
        except Exception as e:
            session.rollback()
            logger.error(f"MetaCognitionStore: record_experience failed ({e})", exc_info=True)
        finally:
            session.close()

    def get_experience(self, agent_id: str) -> list:
        """Get all experience records for an agent."""
        session = self.Session()
        try:
            records = (
                session.query(AgentExperience)
                .filter(AgentExperience.agent_id == agent_id)
                .order_by(AgentExperience.success_count.desc())
                .all()
            )
            return [
                {
                    "agent_id": r.agent_id,
                    "task_pattern": r.task_pattern,
                    "total_tasks": r.total_tasks,
                    "failure_count": r.failure_count,
                    "success_rate": round(float(r.success_count / max(r.total_tasks, 1)), 2),
                    "avg_quality": round(float(r.avg_quality), 2),
                    "best_model": r.best_model,
                    "best_temperature": r.best_temperature,
                }
                for r in records
            ]
        except Exception as e:
            logger.error(f"MetaCognitionStore: get_experience failed ({e})", exc_info=True)
            return []
        finally:
            session.close()

    def get_reliability(self, agent_id: str = "system") -> float:
        """Get current reliability score for an agent. Returns 0.0-1.0 with cache fallback."""
        ReliabilitySession = sessionmaker(bind=self._reliability_engine)
        session = ReliabilitySession()
        try:
            entry = (
                session.query(AgentReliability)
                .filter(AgentReliability.agent_id == agent_id)
                .first()
            )
            score = entry.reliability_score if entry else 1.0
            _RELIABILITY_CACHE[agent_id] = score  # Update cache
            return score
        except Exception as e:
            cached = _RELIABILITY_CACHE.get(agent_id, 1.0)
            logger.warning(
                f"MetaCognitionStore: get_reliability DB error ({e}), using cache fallback: {cached:.2f}"
            )
            return cached
        finally:
            session.close()

    # Phase 11.18.4: Session-level shadow violation counter
    _shadow_violation_counts = {}  # {session_id: count}

    def record_inconsistency(
        self, agent_id: str, session_id: str, claim: str, reasoning_val: Any, reality_val: Any
    ):
        """Phase 11.18.4: Records technical mismatches for Axis 11 auditing."""
        session = self.Session()
        try:
            # We use pattern_notes in MetaRecord to store the delta for now
            note = {
                "type": "inconsistency_evidence",
                "claim": claim,
                "reasoning": reasoning_val,
                "reality": reality_val,
                "axis": 11,
            }
            record = MetaRecord(
                agent_id=agent_id,
                session_id=session_id,
                task=f"Inconsistency: {claim}",
                pattern_notes=json.dumps(note),
                draft_quality=0.0,  # Force zero quality for lying
            )
            session.add(record)
            session.commit()
            logger.info(f"MetaCognition: Inconsistency evidence recorded for {claim} (Axis 11)")
        except Exception as e:
            session.rollback()
            logger.error(f"MetaCognitionStore: Failed to record inconsistency ({e})")
        finally:
            session.close()

    def adjust_reliability(
        self, agent_id: str, delta: float, violation_type: str = "", session_id: str = "default"
    ):
        """
        Adjust agent reliability score using EWMA (Exponentially Weighted Moving Average).
        Backward compatible mapping:
        - delta < 0: legacy penalty, maps to current_score = 0.0
        - 0.0 < delta <= 0.1: legacy success/reward delta, maps to current_score = 1.0
        - otherwise: treated directly as the target current_score [0.0, 1.0]
        """
        ReliabilitySession = sessionmaker(bind=self._reliability_engine)
        session = ReliabilitySession()
        try:
            entry = (
                session.query(AgentReliability)
                .filter(AgentReliability.agent_id == agent_id)
                .first()
            )
            if not entry:
                entry = AgentReliability(agent_id=agent_id, reliability_score=1.0)
                session.add(entry)

            old_score = entry.reliability_score
            ALPHA = 0.3

            # Map delta to EWMA actual_score and classify outcome
            if delta < 0.0:
                actual_score = 0.0
                is_penalty = True
            elif 0.0 < delta <= 0.1:
                actual_score = 1.0
                is_penalty = False
            else:
                actual_score = delta
                is_penalty = (actual_score < 0.5)

            # EWMA formula: s_t = ALPHA * x_t + (1 - ALPHA) * s_{t-1}
            entry.reliability_score = ALPHA * actual_score + (1.0 - ALPHA) * entry.reliability_score
            entry.reliability_score = max(0.0, min(1.0, entry.reliability_score))

            if is_penalty:
                entry.total_violations = (entry.total_violations or 0) + 1
                entry.last_violation_type = violation_type
                entry.last_violation_at = datetime.datetime.now(datetime.UTC)
            else:
                entry.total_successes = (entry.total_successes or 0) + 1
                entry.last_violation_type = ""  # Clear on recovery

                # Crossing threshold recovery message
                if old_score < 0.3 and entry.reliability_score >= 0.3:
                    logger.warning(
                        f"RECOVERY: Agent {agent_id} reliability restored above lock threshold (>=0.3)."
                    )

            entry.updated_at = datetime.datetime.now(datetime.UTC)
            session.commit()

            _RELIABILITY_CACHE[agent_id] = entry.reliability_score  # Update cache

            logger.info(
                f"MetaCognition: {agent_id} reliability -> {entry.reliability_score:.2f} "
                f"(input={delta:+.2f}, mapped_score={actual_score:.2f}, violation={violation_type}, session={session_id})"
            )

            # [SRC:axis_4] Record truth update in Temporal Graph
            try:
                TemporalStore().record_with_supersede(
                    session_id=session_id,
                    event_type="reliability_update",
                    event_key=f"reliability.{agent_id}",
                    extra={
                        "delta": delta,
                        "score": entry.reliability_score,
                        "violation": violation_type,
                    },
                )
            except Exception as te:
                logger.warning(
                    f"MetaCognition: Failed to record temporal fact for {agent_id} ({te})"
                )

            # S4.1: Trigger Auto-Rotation after 2 consecutive shadow verification failures
            if "shadow_verification_failed" in violation_type:
                count = self._shadow_violation_counts.get(session_id, 0) + 1
                self._shadow_violation_counts[session_id] = count
                if count >= 2:
                    logger.error(
                        f"MetaCognition: {count} consecutive shadow failures in {session_id}. TRIGGERING ROTATION."
                    )
                    try:
                        from src.utils.service_locator import get_self_tuner

                        get_self_tuner().apply_rotation(session_id, agent_id, reason=violation_type)
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
