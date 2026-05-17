import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, create_engine
from sqlalchemy.orm import sessionmaker

from src.utils.logging_config import setup_logger

try:
    from .models import MnemosyneBase, Goal
except ImportError:
    from base import Base

logger = setup_logger(__name__)

class GoalStore:
    AXIS_ID = 3

    def __init__(self, db_url: str | None = None):
        from src.utils.project_path import to_absolute_path

        db_url = db_url or f"sqlite:///{to_absolute_path('data/mnemosyne.db')}"
        self.engine = create_engine(
            db_url, connect_args={"check_same_thread": False, "timeout": 30}
        )
        MnemosyneBase.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def add(
        self,
        title: str,
        description: str = "",
        priority: int = 3,
        parent_id: int = None,
        session_id: str = "default",
    ):
        session = self.Session()
        try:
            goal = Goal(
                title=title,
                description=description,
                priority=priority,
                parent_goal_id=parent_id,
                session_id=session_id,
            )
            session.add(goal)
            session.commit()
            gid = goal.id
            return gid
        except Exception as e:
            session.rollback()
            logger.error(f"GoalStore (Axis {self.AXIS_ID}): add failed ({e})", exc_info=True)
            return None
        finally:
            session.close()

    def list_active(self, limit: int = 5):
        session = self.Session()
        try:
            rows = (
                session.query(Goal)
                .filter(Goal.status != "done")
                .order_by(Goal.priority.asc(), Goal.created_at.desc())
                .limit(limit)
                .all()
            )
            return [
                {
                    "id": r.id,
                    "title": r.title,
                    "status": r.status,
                    "priority": r.priority,
                    "description": r.description,
                }
                for r in rows
            ]
        except Exception as e:
            logger.error(
                f"GoalStore (Axis {self.AXIS_ID}): list_active failed ({e})", exc_info=True
            )
            return []
        finally:
            session.close()

    def complete(self, goal_id: int):
        session = self.Session()
        try:
            goal = session.query(Goal).filter(Goal.id == goal_id).first()
            if goal:
                goal.status = "done"
                goal.progress_pct = 100
                goal.completed_at = datetime.datetime.now(datetime.UTC)
                session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"GoalStore (Axis {self.AXIS_ID}): complete failed ({e})", exc_info=True)
        finally:
            session.close()

    def update_progress(self, goal_id: int, pct: float):
        session = self.Session()
        try:
            goal = session.query(Goal).filter(Goal.id == goal_id).first()
            if goal:
                goal.progress_pct = min(100, max(0, pct))
                if pct >= 100:
                    goal.status = "done"
                goal.completed_at = datetime.datetime.now(datetime.UTC)
                session.commit()
        except Exception as e:
            session.rollback()
            logger.error(
                f"GoalStore (Axis {self.AXIS_ID}): update_progress failed ({e})", exc_info=True
            )
        finally:
            session.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        logger.info("=== Mnemosyne Goal Store: Firmitas Test ===")
        store = GoalStore()
        gid = store.add("Test Goal", "Verifying connectivity")
        store.update_progress(gid, 50)
        logger.info(f"Connectivity verified. Goal ID: {gid}")
    else:
        logger.info("Usage: python goal_store.py --test (to run connectivity test)")
