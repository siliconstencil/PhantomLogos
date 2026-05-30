import hashlib
import logging
from typing import Any, cast

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from cognition.mnemosyne.models import (
    EntityRecord,
    FailureMemoryRecord,
    MnemosyneBase,
    ReflectionRecord,
    SemanticRelationRecord,
)
from src.utils.project_path import to_absolute_path

logger = logging.getLogger(__name__)


class ReflectionStore:
    def __init__(self, db_url: str | None = None):
        url = db_url or f"sqlite:///{to_absolute_path('data/mnemosyne.db')}"
        self.engine = create_engine(url, connect_args={"check_same_thread": False, "timeout": 30})
        MnemosyneBase.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def store_entities(self, session_id: str, entities: list[dict[str, Any]]):
        if not entities:
            return
        session = self.Session()
        try:
            for entity in entities:
                name, etype = entity.get("text"), entity.get("type")
                if not name or not etype:
                    continue
                existing = session.query(EntityRecord).filter_by(name=name, type=etype).first()
                if existing:
                    existing.frequency = (existing.frequency or 1) + 1
                    existing.last_seen = __import__("datetime").datetime.now(
                        __import__("datetime").UTC
                    )
                else:
                    session.add(EntityRecord(name=name, type=etype, session_id=session_id))
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def store_relations(self, session_id: str, relations: list[dict[str, Any]]):
        if not relations:
            return
        session = self.Session()
        try:
            for rel in relations:
                session.add(
                    SemanticRelationRecord(
                        subject=rel.get("s"),
                        predicate=rel.get("p"),
                        object=rel.get("o"),
                        session_id=session_id,
                    )
                )
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def store_reflection(
        self, session_id: str, insight: str, category: str = "general", importance: float = 0.5
    ) -> bool:
        if not insight or len(insight) < 20:
            return False
        session = self.Session()
        try:
            session.add(
                ReflectionRecord(
                    insight=insight, category=category, session_id=session_id, importance=importance
                )
            )
            session.commit()
            return True
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()

    def get_recent_reflections(self, limit: int = 5) -> list[dict[str, Any]]:
        session = self.Session()
        try:
            rows = (
                session.query(ReflectionRecord)
                .order_by(ReflectionRecord.created_at.desc())
                .limit(limit)
                .all()
            )
            return [
                {"insight": r.insight, "category": r.category, "created_at": str(r.created_at)}
                for r in rows
            ]
        except Exception:
            return []
        finally:
            session.close()

    def get_relevant_reflections(self, session_id: str, limit: int = 5) -> list[dict[str, Any]]:
        session = self.Session()
        try:
            rows = (
                session.query(ReflectionRecord)
                .filter_by(session_id=session_id)
                .order_by(ReflectionRecord.created_at.desc())
                .limit(limit)
                .all()
            )
            return [{"insight": r.insight} for r in rows]
        except Exception:
            return []
        finally:
            session.close()

    def get_relevant_entities(self, keywords: list[str], limit: int = 10) -> list[dict[str, Any]]:
        if not keywords:
            return []
        session = self.Session()
        try:
            clauses = [EntityRecord.name.like(f"%{k}%") for k in keywords]
            rows = (
                session.query(EntityRecord)
                .filter(*clauses)
                .order_by(EntityRecord.frequency.desc())
                .limit(limit)
                .all()
            )
            return [{"name": r.name, "type": r.type} for r in rows]
        except Exception:
            return []
        finally:
            session.close()

    def get_relevant_relations(self, entities: list[str], limit: int = 10) -> list[dict[str, Any]]:
        if not entities:
            return []
        session = self.Session()
        try:
            rows = (
                session.query(SemanticRelationRecord)
                .filter(
                    SemanticRelationRecord.subject.in_(entities)
                    | SemanticRelationRecord.object.in_(entities)
                )
                .order_by(SemanticRelationRecord.created_at.desc())
                .limit(limit)
                .all()
            )
            return [
                {"subject": r.subject, "predicate": r.predicate, "object": r.object} for r in rows
            ]
        except Exception:
            return []
        finally:
            session.close()

    def store_failure(
        self, error_type: str, root_cause: str, prevention_rule: str, severity: int = 1
    ) -> str:
        if len(prevention_rule) < 50:
            logger.warning(
                f"FailureMemory: Prevention rule too short ({len(prevention_rule)}), skipping."
            )
            return ""
        context_hash = hashlib.sha256(f"{error_type}:{root_cause[:100]}".encode()).hexdigest()[:16]
        session = self.Session()
        try:
            existing = (
                session.query(FailureMemoryRecord).filter_by(context_hash=context_hash).first()
            )
            if existing:
                existing.recurrence_count = (existing.recurrence_count or 1) + 1
                existing.severity = max(existing.severity or 1, severity)
                existing.status = "active"
                existing.updated_at = __import__("datetime").datetime.now(
                    __import__("datetime").UTC
                )
            else:
                session.add(
                    FailureMemoryRecord(
                        error_type=error_type,
                        root_cause=root_cause,
                        prevention_rule=prevention_rule,
                        context_hash=context_hash,
                        severity=severity,
                    )
                )
            session.commit()
            return context_hash
        except Exception as e:
            session.rollback()
            logger.error(f"ReflectionStore: store_failure failed: {e}")
            raise
        finally:
            session.close()

    def get_prevention_rules(self, limit: int = 5) -> list[dict[str, Any]]:
        session = self.Session()
        try:
            rows = (
                session.query(FailureMemoryRecord)
                .filter_by(status="active")
                .order_by(
                    FailureMemoryRecord.severity.desc(), FailureMemoryRecord.recurrence_count.desc()
                )
                .limit(limit)
                .all()
            )
            return [
                {
                    "error_type": r.error_type,
                    "prevention_rule": r.prevention_rule,
                    "recurrence_count": r.recurrence_count,
                    "severity": r.severity,
                }
                for r in rows
            ]
        except Exception:
            return []
        finally:
            session.close()

    def resolve_failure(self, context_hash: str):
        session = self.Session()
        try:
            record = session.query(FailureMemoryRecord).filter_by(context_hash=context_hash).first()
            if record:
                record.status = "archived"
                record.updated_at = __import__("datetime").datetime.now(__import__("datetime").UTC)
                session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
