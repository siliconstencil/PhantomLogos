from src.lachesis.output_guard import get_output_guard
import os

def test_timestamp_guard():
    print(f"--- Timestamp Guardrail Test ---")
    guard = get_output_guard()
    
    # 1. Test output WITHOUT timestamp but require_timestamp=True
    bad_output = "Bu bir test mesajıdır, zaman damgası yok."
    check_fail = guard.check(bad_output, agent_id="sophia", context={"require_timestamp": True})
    
    print("Test 1: Missing timestamp...")
    if check_fail["action"] == "reject" or "missing_timestamp" in check_fail["violations"]:
        print("  [PASS] Output rejected/flagged for missing timestamp.")
    else:
        print("  [FAIL] Guard failed to detect missing timestamp!")
        print(f"  [DEBUG] Result: {check_fail}")

    # 2. Test output WITH timestamp and require_timestamp=True
    good_output = "[1:20 PM PT] Bu geçerli bir mesajdır."
    check_pass = guard.check(good_output, agent_id="sophia", context={"require_timestamp": True})
    
    print("Test 2: Valid timestamp...")
    if "missing_timestamp" not in check_pass["violations"]:
        print("  [PASS] Valid timestamp accepted.")
    else:
        print("  [FAIL] Guard incorrectly flagged valid timestamp!")
        print(f"  [DEBUG] Result: {check_pass}")

    print("--- Test Complete ---")

if __name__ == "__main__":
    test_timestamp_guard()
