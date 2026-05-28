import datetime
import random
import sqlite3
import threading

from sqlalchemy import Column, DateTime, Float, Integer, String, create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker

from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)

OTLBase = declarative_base()


class OTLWeight(OTLBase):
    __tablename__ = "otl_weights"
    id: int = Column(Integer, primary_key=True)  # type: ignore
    node_name: str = Column(String(100), nullable=False)  # type: ignore
    model_tier: str = Column(String(50), nullable=False)  # type: ignore
    weight: float = Column(Float, default=0.0)  # type: ignore
    visits: int = Column(Integer, default=0)  # type: ignore
    last_reward: float = Column(Float, default=0.0)  # type: ignore
    last_updated: datetime.datetime = Column(
        DateTime, default=lambda: datetime.datetime.now(datetime.UTC)
    )  # type: ignore

    def __repr__(self) -> str:
        return f"<OTLWeight node={self.node_name} tier={self.model_tier} w={self.weight:.3f} v={self.visits}>"


class OTLQueryResult:
    def __init__(
        self, node_name: str, best_tier: str, weight: float, confidence: float, epsilon: float
    ) -> None:
        self.node_name = node_name
        self.best_tier = best_tier
        self.weight = weight
        self.confidence = confidence
        self.epsilon = epsilon


class OTLEngine:
    EWMA_ALPHA = 0.15
    EPSILON_INIT = 0.1
    EPSILON_MIN = 0.05
    EPSILON_DECAY = 0.995
    MIN_TRAJECTORIES_BEFORE_DECAY = 50

    def __init__(self, db_url: str | None = None) -> None:
        from src.utils.project_path import to_absolute_path

        db_url = db_url or f"sqlite:///{to_absolute_path('data/mnemosyne.db')}"
        self.engine: Engine = create_engine(
            db_url, connect_args={"check_same_thread": False, "timeout": 30}
        )

        @event.listens_for(self.engine, "connect")
        def _set_wal_pragma(
            dbapi_connection: sqlite3.Connection, _connection_record: object
        ) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA synchronous=NORMAL;")
            cursor.execute("PRAGMA cache_size=-65536;")
            cursor.close()

        OTLBase.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self._lock = threading.Lock()
        self._total_trajectories = 0

    def _get_epsilon(self) -> float:
        if self._total_trajectories < self.MIN_TRAJECTORIES_BEFORE_DECAY:
            return self.EPSILON_INIT
        decay_steps = self._total_trajectories - self.MIN_TRAJECTORIES_BEFORE_DECAY
        return max(self.EPSILON_MIN, self.EPSILON_INIT * (self.EPSILON_DECAY**decay_steps))

    def _load_tier_options(self, node_name: str) -> list[str]:
        base = ["ultra_light", "light", "primary", "expert"]
        return [t for t in base if t in self._get_allowed_tiers(node_name)]

    def _get_allowed_tiers(self, node_name: str) -> set[str]:
        node_tier_map = {
            "draft": {"ultra_light", "light", "primary", "expert"},
            "expert_draft": {"expert"},
            "critique": {"primary", "expert"},
            "verify": {"primary", "expert"},
            "tool_exec": {"primary", "expert"},
            "refine": {"primary", "expert"},
            "reflection": {"light", "primary"},
            "anchor_inject": {"light", "primary", "expert"},
            "vision": {"expert"},
            "deadlock_resolver": {"light", "primary"},
        }
        return node_tier_map.get(node_name, {"primary", "expert"})

    def get_or_create_weight(self, node_name: str, model_tier: str) -> OTLWeight:
        with self._lock:
            sess = self.Session()
            try:
                record = (
                    sess.query(OTLWeight)
                    .filter_by(node_name=node_name, model_tier=model_tier)
                    .first()
                )
                if not record:
                    record = OTLWeight(
                        node_name=node_name, model_tier=model_tier, weight=0.0, visits=0
                    )
                    sess.add(record)
                    sess.commit()
                    sess.refresh(record)
                return record
            except Exception as e:
                sess.rollback()
                logger.error(f"otl_engine: get_or_create_weight failed ({e})")
                raise
            finally:
                sess.close()

    def update_weight(self, node_name: str, model_tier: str, reward: float) -> None:
        if reward < -1.0 or reward > 1.0:
            reward = max(-1.0, min(1.0, reward))
        with self._lock:
            sess = self.Session()
            try:
                record = (
                    sess.query(OTLWeight)
                    .filter_by(node_name=node_name, model_tier=model_tier)
                    .first()
                )
                if not record:
                    record = OTLWeight(
                        node_name=node_name, model_tier=model_tier, weight=0.0, visits=0
                    )
                    sess.add(record)
                    sess.flush()

                record.weight = self.EWMA_ALPHA * reward + (1 - (self.EWMA_ALPHA)) * record.weight
                record.visits += 1
                record.last_reward = reward
                record.last_updated = datetime.datetime.now(datetime.UTC)
                sess.commit()
                logger.info(
                    f"otl_engine: Updated weight for ({node_name}, {model_tier}): "
                    f"w={record.weight:.3f} v={record.visits} r={reward:.3f}"
                )
            except Exception as e:
                sess.rollback()
                logger.error(f"otl_engine: update_weight failed ({e})")
            finally:
                sess.close()

    def select_tier(self, node_name: str) -> OTLQueryResult:
        epsilon = self._get_epsilon()
        allowed = list(self._get_allowed_tiers(node_name))

        explore = random.random() < epsilon  # noqa: S311
        if explore or not allowed:
            chosen = random.choice(allowed) if allowed else "primary"  # noqa: S311
            logger.info(
                f"otl_engine: EXPLORE for '{node_name}' -> {chosen} (epsilon={epsilon:.3f})"
            )
            return OTLQueryResult(
                node_name=node_name,
                best_tier=chosen,
                weight=0.0,
                confidence=0.0,
                epsilon=epsilon,
            )

        with self._lock:
            sess = self.Session()
            try:
                records = (
                    sess.query(OTLWeight)
                    .filter(OTLWeight.node_name == node_name, OTLWeight.model_tier.in_(allowed))
                    .order_by(OTLWeight.weight.desc())
                    .all()
                )
                if not records:
                    chosen = allowed[0]
                    logger.info(
                        f"otl_engine: No OTL data for '{node_name}', defaulting to {chosen}"
                    )
                    return OTLQueryResult(
                        node_name=node_name,
                        best_tier=chosen,
                        weight=0.0,
                        confidence=0.0,
                        epsilon=epsilon,
                    )

                best = records[0]
                runner_up_weight = records[1].weight if len(records) > 1 else -1.0
                confidence = 0.5
                if best.visits >= 3:
                    spread = best.weight - runner_up_weight if runner_up_weight > -1.0 else 0.5
                    confidence = min(0.95, 0.5 + (spread * 2.0))

                logger.info(
                    f"otl_engine: EXPLOIT for '{node_name}' -> {best.model_tier} "
                    f"(w={best.weight:.3f} v={best.visits} c={confidence:.2f})"
                )
                return OTLQueryResult(
                    node_name=node_name,
                    best_tier=best.model_tier,
                    weight=best.weight,
                    confidence=confidence,
                    epsilon=epsilon,
                )
            except Exception as e:
                sess.rollback()
                logger.error(f"otl_engine: select_tier failed ({e})")
                return OTLQueryResult(
                    node_name=node_name,
                    best_tier=allowed[0] if allowed else "primary",
                    weight=0.0,
                    confidence=0.0,
                    epsilon=epsilon,
                )
            finally:
                sess.close()

    def to_dict(self) -> dict:
        with self._lock:
            sess = self.Session()
            try:
                records = (
                    sess.query(OTLWeight)
                    .order_by(OTLWeight.node_name, OTLWeight.weight.desc())
                    .all()
                )
                return {
                    "weights": [
                        {
                            "node_name": r.node_name,
                            "model_tier": r.model_tier,
                            "weight": round(float(r.weight or 0.0), 3),
                            "visits": r.visits,
                            "last_reward": round(float(r.last_reward or 0.0), 3),
                        }
                        for r in records
                    ]
                }
            except Exception:
                return {"weights": []}
            finally:
                sess.close()


_OTL_ENGINE_INSTANCE = None
_OTL_LOCK = threading.RLock()


def get_otl_engine() -> OTLEngine:
    global _OTL_ENGINE_INSTANCE
    if _OTL_ENGINE_INSTANCE is None:
        with _OTL_LOCK:
            if _OTL_ENGINE_INSTANCE is None:
                _OTL_ENGINE_INSTANCE = OTLEngine()
    return _OTL_ENGINE_INSTANCE
