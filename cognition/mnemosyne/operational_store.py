from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

from src.utils.logging_config import setup_logger

from .models import MnemosyneBase, OperationalLog

logger = setup_logger(__name__)


class OperationalStore:
    """
    Mnemosyne Operational Memory Layer (Axis 7).
    Manages system telemetry, tool usage tracking, and self-awareness reporting.
    """

    AXIS_ID = 7

    def __init__(self, db_url: str | None = None):
        from src.utils.project_path import to_absolute_path

        db_url = db_url or f"sqlite:///{to_absolute_path('data/mnemosyne.db')}"
        self.engine = create_engine(
            db_url, connect_args={"check_same_thread": False, "timeout": 30}
        )
        MnemosyneBase.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def record_event(
        self,
        name: str,
        level: str,
        message: str,
        agent_id: str = "system",
        tool_name: str | None = None,
        session_id: str = "default",
    ):
        session = self.Session()
        try:
            log = OperationalLog(
                name=name,
                level=level,
                message=message,
                agent_id=agent_id,
                tool_name=tool_name,
                session_id=session_id,
            )
            session.add(log)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"OperationalStore: record_event failed ({e})")
        finally:
            session.close()

    def get_recent_logs(self, limit: int = 50):
        session = self.Session()
        try:
            logs = (
                session.query(OperationalLog)
                .order_by(OperationalLog.timestamp.desc())
                .limit(limit)
                .all()
            )
            return logs
        finally:
            session.close()

    def get_usage_report(self) -> dict:
        """
        Self-awareness reporting: returns tool usage stats, top agents, and event counts.
        Provides the system with a real-time operational transparency snapshot.
        """
        session = self.Session()
        try:
            total_events = session.query(func.count(OperationalLog.id)).scalar() or 0

            top_tools = (
                session.query(
                    OperationalLog.tool_name, func.count(OperationalLog.id).label("calls")
                )
                .filter(OperationalLog.tool_name.isnot(None))
                .group_by(OperationalLog.tool_name)
                .order_by(func.count(OperationalLog.id).desc())
                .limit(5)
                .all()
            )

            agent_activity = (
                session.query(
                    OperationalLog.agent_id, func.count(OperationalLog.id).label("events")
                )
                .group_by(OperationalLog.agent_id)
                .order_by(func.count(OperationalLog.id).desc())
                .limit(5)
                .all()
            )

            recent_errors = (
                session.query(func.count(OperationalLog.id))
                .filter(OperationalLog.level == "ERROR")
                .scalar()
                or 0
            )

            last_event = (
                session.query(OperationalLog).order_by(OperationalLog.timestamp.desc()).first()
            )

            return {
                "total_events": total_events,
                "top_tools": [{"tool": t[0], "calls": t[1]} for t in top_tools],
                "agent_activity": [{"agent": a[0], "events": a[1]} for a in agent_activity],
                "error_count": recent_errors,
                "last_event_at": last_event.timestamp.isoformat() if last_event else None,
                "health": "healthy" if recent_errors < total_events * 0.1 else "degraded",
            }
        except Exception as e:
            logger.error(f"OperationalStore: get_usage_report failed ({e})")
            return {"error": str(e)}
        finally:
            session.close()
