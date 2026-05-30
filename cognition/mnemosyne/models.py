import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base

MnemosyneBase = declarative_base()
ReliabilityBase = declarative_base()
SpatialBase = declarative_base()


class Episode(MnemosyneBase):
    __tablename__ = "episodes"
    id: int = Column(Integer, primary_key=True)
    session_id: str = Column(String(64), nullable=False)
    agent_id: str = Column(String(50), default="system")
    action = Column(String(255), nullable=False)
    detail = Column(Text)
    outcome = Column(String(50), default="pending")
    tokens_used = Column(Integer, default=0)
    latency_ms = Column(Float, default=0)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))

    __table_args__ = (
        Index("idx_episodes_session", "session_id"),
        Index("idx_agent_timestamp", "agent_id", "created_at"),
    )


class Event(MnemosyneBase):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True)
    session_id = Column(String(64), nullable=False)
    seq_num = Column(Integer, nullable=False)
    event_type = Column(String(100), nullable=False)
    agent_id = Column(String(50), default="system")
    payload = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))

    __table_args__ = (Index("idx_events_session", "session_id"),)


class ToolPath(MnemosyneBase):
    __tablename__ = "tool_paths"
    id = Column(Integer, primary_key=True)
    agent_id = Column(String(50), default="system")
    tool_name = Column(String(100), nullable=False)
    task_type = Column(String(100), nullable=False)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    avg_latency_ms = Column(Float, default=0)
    last_used = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))
    notes = Column(Text)

    __table_args__ = (Index("idx_tool_paths_task", "task_type"),)


class Goal(MnemosyneBase):
    __tablename__ = "goals"
    id: int = Column(Integer, primary_key=True)
    agent_id: str = Column(String(50), default="system")
    session_id: str = Column(String(64), default="")
    title: str = Column(String(255), nullable=False)
    description: str | None = Column(Text)
    status: str = Column(String(50), default="pending")
    priority: int = Column(Integer, default=3)
    parent_goal_id: int | None = Column(Integer, nullable=True)
    progress_pct: float = Column(Float, default=0)
    created_at: datetime.datetime = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))
    completed_at: datetime.datetime | None = Column(DateTime, nullable=True)

    __table_args__ = (Index("idx_goals_active", "status", "priority"),)


class OperationalLog(MnemosyneBase):
    __tablename__ = "operational_logs_v2"
    id: int = Column(Integer, primary_key=True)
    timestamp: datetime.datetime = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))
    session_id: str = Column(String(100), default="default")
    agent_id: str = Column(String(50), default="system")
    tool_name: str | None = Column(String(50))
    name = Column(String(100))
    level = Column(String(20))
    message = Column(Text)


class MetaRecord(MnemosyneBase):
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
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))

    __table_args__ = (Index("idx_refl_session", "session_id"),)


class AgentExperience(MnemosyneBase):
    __tablename__ = "agent_experience"
    id: int = Column(Integer, primary_key=True)
    agent_id: str = Column(String(50), nullable=False)
    session_id: str = Column(String(64), default="")
    task_pattern: str = Column(String(100), default="general")
    total_tasks: int = Column(Integer, default=0)
    success_count: int = Column(Integer, default=0)
    failure_count: int = Column(Integer, default=0)
    avg_quality: float = Column(Float, default=0.5)
    best_model: str = Column(String(100), default="")
    best_temperature: float = Column(Float, default=0.3)
    created_at: datetime.datetime = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))
    updated_at: datetime.datetime = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))

    __table_args__ = (Index("idx_exp_agent", "agent_id", "task_pattern"),)


class GovernanceRule(MnemosyneBase):
    __tablename__ = "governance_rules"
    id: int = Column(Integer, primary_key=True)
    rule_id: str = Column(String(50), unique=True, nullable=False)
    agent_id: str = Column(String(50), default="system")
    description: str = Column(Text, nullable=False)
    severity: int = Column(Integer, default=1)
    active: int = Column(Integer, default=1)
    created_at: datetime.datetime = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))


class Fact(MnemosyneBase):
    __tablename__ = "facts"
    id = Column(Integer, primary_key=True)
    agent_id = Column(String(50), default="global")
    subject = Column(String(255), nullable=False)
    predicate = Column(String(255))
    object = Column(Text, nullable=False)
    source = Column(String(255))
    confidence = Column(Float, default=1.0)
    last_verified = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))

    __table_args__ = (Index("idx_rel_subject", "subject"),)


class ToneRecord(MnemosyneBase):
    __tablename__ = "tone_history"
    id = Column(Integer, primary_key=True)
    session_id = Column(String(64), nullable=False)
    tone = Column(String(50), default="neutral")
    urgency = Column(Float, default=0.5)
    verbosity = Column(Float, default=0.5)
    original_message = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))


class EntityRecord(MnemosyneBase):
    __tablename__ = "entities"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    session_id = Column(String, nullable=True)
    frequency = Column(Integer, default=1)
    last_seen = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))

    __table_args__ = (UniqueConstraint("name", "type"),)


class ReflectionRecord(MnemosyneBase):
    __tablename__ = "reflections"
    id = Column(Integer, primary_key=True, autoincrement=True)
    insight = Column(Text, nullable=False)
    category = Column(String, default="general")
    session_id = Column(String, nullable=True)
    importance = Column(Float, default=0.5)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))


class SemanticRelationRecord(MnemosyneBase):
    __tablename__ = "semantic_relations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    subject = Column(String, nullable=False)
    predicate = Column(String, nullable=True)
    object = Column(String, nullable=False)
    session_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))


class FailureMemoryRecord(MnemosyneBase):
    __tablename__ = "failure_memory"
    id: int = Column(Integer, primary_key=True, autoincrement=True)
    error_type: str = Column(String, nullable=False)
    root_cause: str | None = Column(Text, nullable=True)
    prevention_rule: str | None = Column(Text, nullable=True)
    context_hash: str = Column(String, unique=True, nullable=False)
    severity: int = Column(Integer, default=1)
    recurrence_count: int = Column(Integer, default=1)
    status: str = Column(String, default="active")
    created_at: datetime.datetime = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))
    updated_at: datetime.datetime = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))


class VisualMemory(MnemosyneBase):
    __tablename__ = "visual_memories"
    id = Column(Integer, primary_key=True)
    image_hash = Column(String(64), index=True)
    description = Column(Text)
    vector = Column(LargeBinary)
    source_path = Column(String(512))
    variant = Column(String(50))
    metadata_json = Column(Text)
    session_id = Column(String(100), index=True)
    timestamp = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))


class AgentReliability(ReliabilityBase):
    __tablename__ = "agent_reliability"
    id: int = Column(Integer, primary_key=True)
    agent_id: str = Column(String(50), nullable=False, unique=True)
    reliability_score: float = Column(Float, default=1.0)
    total_violations: int = Column(Integer, default=0)
    total_successes: int = Column(Integer, default=0)
    cycle_count: int = Column(Integer, default=0)
    last_violation_type: str | None = Column(String(50))
    last_violation_at: datetime.datetime | None = Column(DateTime)
    updated_at: datetime.datetime = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))


class ModuleNode(SpatialBase):
    __tablename__ = "spatial_modules"
    id: int = Column(Integer, primary_key=True)
    module_name: str = Column(String(255), nullable=False, unique=True)
    file_path: str = Column(String(512))
    line_count: int = Column(Integer, default=0)
    num_functions: int = Column(Integer, default=0)
    content_hash: str = Column(String(64))
    last_indexed: datetime.datetime = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))


class DependencyEdge(SpatialBase):
    __tablename__ = "spatial_edges"
    id = Column(Integer, primary_key=True)
    source_module = Column(String(255), nullable=False, index=True)
    target_module = Column(String(255), nullable=False, index=True)
    relationship = Column(String(50), default="imports")
    depth = Column(Integer, default=1)
