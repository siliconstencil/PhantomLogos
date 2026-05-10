from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, JSON
from sqlalchemy.orm import sessionmaker
import datetime
import os
from src.utils.logging_config import setup_logger
try:
    from .base import Base
except ImportError:
    from base import Base

logger = setup_logger(__name__)

class GovernanceRule(Base):
    """Strict rules and policies that the agent MUST follow."""
    __tablename__ = 'governance_rules'
    id = Column(Integer, primary_key=True)
    rule_id = Column(String(50), unique=True, nullable=False)
    agent_id = Column(String(50), default="system")
    description = Column(Text, nullable=False)
    severity = Column(Integer, default=1)
    active = Column(Integer, default=1)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

class Fact(Base):
    """Verified pieces of information and truth-anchors."""
    __tablename__ = 'facts'
    id = Column(Integer, primary_key=True)
    agent_id = Column(String(50), default="global")
    subject = Column(String(255), nullable=False)
    predicate = Column(String(255))
    object = Column(Text, nullable=False)
    source = Column(String(255))
    confidence = Column(Float, default=1.0)
    last_verified = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

class MnemosyneRationalStore:
    """
    Mnemosyne Rational Memory Layer using SQLAlchemy (SQLite/PostgreSQL).
    Manages Facts and Governance rules.
    """
    AXIS_ID = 10

    def __init__(self, db_url: str = "sqlite:///data/mnemosyne.db"):
        os.makedirs("data", exist_ok=True)
        self.engine = create_engine(db_url, connect_args={"check_same_thread": False})
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def add_rule(self, rule_id: str, description: str, agent_id: str = "system", severity: int = 3):
        session = self.Session()
        try:
            rule = GovernanceRule(rule_id=rule_id, description=description, agent_id=agent_id, severity=severity)
            session.merge(rule)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"MnemosyneRationalStore (Axis {self.AXIS_ID}): add_rule failed ({e})", exc_info=True)
        finally:
            session.close()

    def add_fact(self, subject: str, obj: str, agent_id: str = "global", predicate: str = "is", source: str = "user"):
        session = self.Session()
        try:
            fact = Fact(subject=subject, object=obj, agent_id=agent_id, predicate=predicate, source=source)
            session.add(fact)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"MnemosyneRationalStore (Axis {self.AXIS_ID}): add_fact failed ({e})", exc_info=True)
        finally:
            session.close()

    def get_secure_rules(self, agent_id: str) -> list:
        """RLS: Returns only rules applicable to the specific agent or system-wide."""
        session = self.Session()
        try:
            rules = session.query(GovernanceRule).filter(
                (GovernanceRule.active == 1) & 
                ((GovernanceRule.agent_id == agent_id) | (GovernanceRule.agent_id == "system"))
            ).all()
            return [{"id": r.rule_id, "desc": r.description} for r in rules]
        except Exception as e:
            logger.error(f"MnemosyneRationalStore (Axis {self.AXIS_ID}): get_secure_rules failed ({e})", exc_info=True)
            return []
        finally:
            session.close()

    def get_secure_facts(self, agent_id: str) -> list:
        """RLS: Returns only facts owned by the agent or marked as global."""
        session = self.Session()
        try:
            facts = session.query(Fact).filter(
                (Fact.agent_id == agent_id) | (Fact.agent_id == "global")
            ).all()
            return [{"subject": f.subject, "object": f.object} for f in facts]
        except Exception as e:
            logger.error(f"MnemosyneRationalStore (Axis {self.AXIS_ID}): get_secure_facts failed ({e})", exc_info=True)
            return []
        finally:
            session.close()

if __name__ == "__main__":
    # Firmitas Test
    store = MnemosyneRationalStore()
    store.add_rule("EMOJI_BAN", "Do not use emojis.", agent_id="system")
    store.add_rule("PRIVATE_RULE", "Only for Sophia Agent.", agent_id="sophia")
    store.add_fact("Project Name", "Antigravity", agent_id="global")
    
    logger.info(f"Rules for Sophia: {store.get_secure_rules('sophia')}")
    logger.info(f"Rules for Generic: {store.get_secure_rules('generic')}")
    logger.info("Mnemosyne Secure Rational Store verified.")
