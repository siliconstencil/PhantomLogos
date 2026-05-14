import asyncio
import os
import sqlite3

from src.clotho.control_handoff import clotho_handoff
from src.utils.project_path import get_project_root


async def verify():
    project_root = get_project_root()
    db_mnemosyne = os.path.join(project_root, "data/mnemosyne.db")
    db_reliability = os.path.join(project_root, "data/reliability.db")

    print("--- Green Chain Verification ---")

    # 1. Run a simple task
    task = "Verify system integrity and axis connectivity."
    session_id = "test_verification_session"
    print(f"Triggering task: {task}")

    try:
        await clotho_handoff(task, session_id=session_id)
    except Exception as e:
        print(
            f"Task execution failed (Expected if models are slow, but we only check DB injections): {e}"
        )

    # 2. Check Axis 3 (Goals)
    conn = sqlite3.connect(db_mnemosyne)
    goals = conn.execute("SELECT title FROM goals WHERE session_id = ?", (session_id,)).fetchall()
    print(f"Axis 3 (Goals) check: {'OK' if goals else 'FAIL'} ({len(goals)} goals found)")

    # 3. Check Axis 9 (Tone)
    tones = conn.execute(
        "SELECT original_message FROM tone_history WHERE session_id = ?", (session_id,)
    ).fetchall()
    print(f"Axis 9 (Tone) check: {'OK' if tones else 'FAIL'} ({len(tones)} tones found)")

    # 4. Check Axis 8 (Meta-Cog / Experience)
    conn_rel = sqlite3.connect(db_reliability)
    exp = conn_rel.execute(
        "SELECT agent_id FROM agent_experience WHERE session_id = ?", (session_id,)
    ).fetchall()
    print(f"Axis 8 (Experience) check: {'OK' if exp else 'FAIL'} ({len(exp)} records found)")

    conn.close()
    conn_rel.close()


if __name__ == "__main__":
    asyncio.run(verify())
