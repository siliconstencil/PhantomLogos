import asyncio
import os
import sqlite3

from src.clotho.bridge.base import ToolBridge


async def audit_gap_2():
    print("--- GAP 2: Agent-Aware Telemetry Audit ---")
    session_id = "audit_session_gap_2"
    agent_id = "sophia_auditor"

    # 1. Execute a tool via ToolBridge
    bridge = ToolBridge(session_id, agent_id=agent_id)
    print(f"Executing 'report' tool as {agent_id}...")
    result = await bridge.execute("report", {})

    # 2. Check Database for the record
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "data", "mnemosyne.db")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("Verifying operational_logs_v2 for the record...")
    cursor.execute(
        """
        SELECT agent_id, tool_name, session_id
        FROM operational_logs_v2
        WHERE session_id = ? AND agent_id = ?
        LIMIT 1
    """,
        (session_id, agent_id),
    )

    row = cursor.fetchone()
    if row:
        print(f"  [PASS] Record found: Agent={row[0]}, Tool={row[1]}, Session={row[2]}")
    else:
        print("  [FAIL] Record not found in operational_logs_v2.")

    conn.close()
    print("--- Audit Complete ---")


if __name__ == "__main__":
    asyncio.run(audit_gap_2())
