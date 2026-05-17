"""
Mnemosyne Creative/Tone Memory Layer (Axis 9).
Persona adaptation and user message tone analysis.
"""

import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)

from .models import MnemosyneBase, ToneRecord

TONE_KEYWORDS = {
    "urgent": ["urgent", "asap", "immediately", "quick", "fast", "hurry"],
    "frustrated": ["bug", "error", "broken", "fail", "wrong", "stupid", "hate"],
    "creative": ["idea", "design", "think", "imagine", "create", "style"],
    "analytical": ["data", "report", "stats", "logic", "reason", "proof"],
    "casual": ["hey", "hi", "hello", "thanks", "ok", "cool"]
}

class ToneStore:
    AXIS_ID = 9

    def __init__(self, db_url: str | None = None):
        from src.utils.project_path import to_absolute_path

        db_url = db_url or f"sqlite:///{to_absolute_path('data/mnemosyne.db')}"
        self.engine = create_engine(
            db_url, connect_args={"check_same_thread": False, "timeout": 30}
        )
        MnemosyneBase.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def analyze_tone(self, message: str) -> dict:
        """Simple keyword-based tone classifier."""
        msg_lower = message.lower()
        scores = {}
        for tone, keywords in TONE_KEYWORDS.items():
            scores[tone] = sum(1 for kw in keywords if kw in msg_lower)

        if scores.get("urgent", 0) >= 2:
            tone = "urgent"
        elif scores.get("frustrated", 0) >= 2:
            tone = "frustrated"
        elif scores.get("creative", 0) >= 2:
            tone = "creative"
        elif scores.get("analytical", 0) >= 2:
            tone = "analytical"
        elif scores.get("casual", 0) >= 1:
            tone = "casual"
        else:
            tone = "neutral"

        urgency = min(1.0, scores.get("urgent", 0) * 0.5 + scores.get("frustrated", 0) * 0.3)
        verbosity = "short" if len(message) < 50 else ("long" if len(message) > 500 else "normal")

        return {"tone": tone, "urgency": urgency, "verbosity": verbosity}

    def record_tone(self, session_id: str, message: str):
        analysis = self.analyze_tone(message)
        session = self.Session()
        try:
            record = ToneRecord(
                session_id=session_id,
                tone=analysis["tone"],
                urgency=analysis["urgency"],
                verbosity=analysis["verbosity"],
                original_message=message[:500],
            )
            session.add(record)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(
                f"ToneStore (Axis {self.AXIS_ID}): record_tone failed ({e})", exc_info=True
            )
        finally:
            session.close()

    def get_recent_tone(self, session_id: str, limit: int = 3) -> str:
        session = self.Session()
        try:
            records = (
                session.query(ToneRecord)
                .filter(ToneRecord.session_id == session_id)
                .order_by(ToneRecord.created_at.desc())
                .limit(limit)
                .all()
            )
            if records:
                tones = [r.tone for r in records]
                return max(set(tones), key=tones.count)
            return "neutral"
        except Exception as e:
            logger.error(f"ToneStore (Axis {self.AXIS_ID}): get_recent_tone failed ({e})")
            return "neutral"
        finally:
            session.close()


if __name__ == "__main__":
    logger.info("=== Mnemosyne Tone Store: Firmitas Test ===")
    store = ToneStore()
    result = store.analyze_tone("Hey, can you urgently fix this bug?")
    logger.info(f"Tone test: {result}")
    store.record_tone("test_session", "Hey, can you urgently fix this bug?")
    recent = store.get_recent_tone("test_session")
    logger.info(f"Recent tone: {recent}")
