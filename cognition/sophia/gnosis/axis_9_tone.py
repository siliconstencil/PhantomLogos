from ...mnemosyne.tone_store import ToneStore


def _build_axis_9(session_id: str, task_hint: str) -> str:
    lines = []
    try:
        store = ToneStore()
        recent = store.get_recent_tone(session_id)
        if recent == "neutral":
            # Fallback: cross-session query. Retrieve from any recent sessions.
            session = store.Session()
            try:
                from cognition.mnemosyne.tone_store import ToneRecord

                records = (
                    session.query(ToneRecord).order_by(ToneRecord.created_at.desc()).limit(20).all()
                )
                if records:
                    tones = [r.tone for r in records if r.tone != "neutral"]
                    if tones:
                        recent = max(set(tones), key=tones.count)
            except Exception:
                pass
            finally:
                session.close()

        if recent != "neutral":
            lines.append("### MNEMOSYNE AXIS 9 (USER TONE)")
            lines.append(f"Tone detected: {recent}")
    except Exception:
        pass
    return "\n".join(lines)
