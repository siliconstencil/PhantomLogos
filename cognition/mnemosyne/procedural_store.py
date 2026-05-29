import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.utils.logging_config import setup_logger

try:
    from .models import MnemosyneBase, ToolPath
    from .temporal_store import TemporalStore
except ImportError:
    from .temporal_store import TemporalStore

logger = setup_logger(__name__)


class ProceduralStore:
    AXIS_ID = 2

    def __init__(self, db_url: str | None = None):
        from src.utils.project_path import to_absolute_path

        db_url = db_url or f"sqlite:///{to_absolute_path('data/mnemosyne.db')}"
        self.engine = create_engine(
            db_url, connect_args={"check_same_thread": False, "timeout": 30}
        )
        MnemosyneBase.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def record_usage(self, tool_name: str, task_type: str, success: bool, latency_ms: float = 0):
        session = self.Session()
        try:
            row = (
                session.query(ToolPath)
                .filter(ToolPath.tool_name == tool_name, ToolPath.task_type == task_type)
                .first()
            )
            if row:
                if success:
                    row.success_count += 1
                else:
                    row.failure_count += 1
                row.avg_latency_ms = (row.avg_latency_ms + latency_ms) / 2
                row.last_used = datetime.datetime.now(datetime.UTC)
            else:
                row = ToolPath(
                    tool_name=tool_name,
                    task_type=task_type,
                    success_count=1 if success else 0,
                    failure_count=0 if success else 1,
                    avg_latency_ms=latency_ms,
                )
                session.add(row)
            session.commit()

            # [SRC:axis_4] Record truth update in Temporal Graph
            try:
                # We use a dummy session_id for background store updates or pass it if available
                TemporalStore().record_with_supersede(
                    session_id="system_procedural",
                    event_type="tool_performance",
                    event_key=f"tool_perf.{tool_name}.{task_type}",
                    latency_ms=latency_ms,
                    extra={"success": success, "avg_latency": row.avg_latency_ms},
                )
            except Exception as te:
                logger.warning(
                    f"ProceduralStore: Failed to record temporal fact for {tool_name} ({te})"
                )
        except Exception as e:
            session.rollback()
            logger.error(
                f"ProceduralStore (Axis {self.AXIS_ID}): record_usage failed ({e})", exc_info=True
            )
        finally:
            session.close()

    def best_tool(self, task_type: str):
        session = self.Session()
        try:
            rows = (
                session.query(ToolPath)
                .filter(ToolPath.task_type == task_type)
                .order_by(ToolPath.success_count.desc())
                .limit(3)
                .all()
            )
            success_rates = []
            for r in rows:
                total = r.success_count + r.failure_count
                rate = r.success_count / total if total > 0 else 0
                success_rates.append((r.tool_name, rate, r.avg_latency_ms))
            return sorted(success_rates, key=lambda x: x[1], reverse=True)
        except Exception as e:
            logger.error(
                f"ProceduralStore (Axis {self.AXIS_ID}): best_tool failed ({e})", exc_info=True
            )
            return []
        finally:
            session.close()


if __name__ == "__main__":
    logger.info("=== Mnemosyne Procedural Store: Firmitas Test ===")
    store = ProceduralStore()
    store.record_usage("test_tool", "test_task", success=True, latency_ms=150)
    best = store.best_tool("test_task")
    logger.info(f"Connectivity verified. Best tool: {best}")
