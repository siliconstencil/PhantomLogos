import os
import sys

from sqlalchemy import text

# Set project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from cognition.sophia.hephaestus import _get_episodic


def check_thinking_logs():
    print("--- [Thinking CoT Audit] ---")
    episodic = _get_episodic()
    with episodic.engine.connect() as conn:
        # Check for Thinking/CoT indicators in detail field
        query = text("""
            SELECT session_id, tokens_used, latency_ms, detail
            FROM episodes
            WHERE detail LIKE '%Model:%'
            ORDER BY id DESC
            LIMIT 10
        """)
        rows = conn.execute(query).fetchall()

        if not rows:
            print("No model logs found in episodic store.")
            return

        for row in rows:
            sid, tokens, lat, detail = row
            # Look for evidence of thinking/thoughts in the metadata
            # Gemini 3 responses usually have thoughts_token_count if tracked
            print(f"Session: {sid} | Tokens: {tokens} | Latency: {lat:.1f}ms")
            print(f"  Detail: {detail}")

            # Check if 'thoughts' or 'thinking' is mentioned in the detail (logged by sophia.py)
            if "thoughts" in detail.lower() or "thinking" in detail.lower():
                print("  [OK] Thinking/CoT detected in this session.")
            else:
                print("  [WARN] No explicit 'thoughts' metadata in this log.")


if __name__ == "__main__":
    check_thinking_logs()
