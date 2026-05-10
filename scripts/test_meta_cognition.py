import sqlite3
import os
import time
from cognition.mnemosyne.meta_cognition import MetaCognitionStore

def test_meta_records():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "data", "mnemosyne.db")
    
    print(f"--- Meta-Cognition (Axis 8) Test ---")
    store = MetaCognitionStore()
    
    test_session = f"meta_session_{int(time.time())}"
    test_agent = "sophia_meta_test"
    
    # 1. Test record()
    print(f"Recording test score for {test_agent}...")
    store.record(
        agent_id=test_agent,
        score=0.95,
        flaws=["none"],
        session_id=test_session
    )
    
    # 2. Test adjust_reliability()
    print(f"Adjusting reliability for {test_agent}...")
    store.adjust_reliability(
        agent_id=test_agent,
        delta=-0.05,
        violation_type="test_violation"
    )
    
    # Give it a bit
    time.sleep(0.5)
    
    # 3. Verify in DB
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Verifying meta_cognition table...")
    cursor.execute("SELECT draft_quality, session_id FROM meta_cognition WHERE agent_id = ? ORDER BY id DESC LIMIT 1", (test_agent,))
    res_record = cursor.fetchone()
    
    if res_record and res_record[0] == 0.95:
        print(f"  [PASS] Meta record found (Score: {res_record[0]})")
    else:
        print(f"  [FAIL] Meta record missing or incorrect.")

    # 4. Verify Reliability in reliability.db
    rel_db_path = os.path.join(base_dir, "data", "reliability.db")
    conn_rel = sqlite3.connect(rel_db_path)
    cursor_rel = conn_rel.cursor()
    
    print("Verifying agent_reliability table in reliability.db...")
    cursor_rel.execute("SELECT reliability_score FROM agent_reliability WHERE agent_id = ?", (test_agent,))
    res_rel = cursor_rel.fetchone()
    
    if res_rel:
        print(f"  [PASS] Reliability score found: {res_rel[0]}")
    else:
        print(f"  [FAIL] Reliability score missing in reliability.db.")

    conn_rel.close()
    conn.close()
    print("--- Test Complete ---")

if __name__ == "__main__":
    test_meta_records()
