import sys
from pathlib import Path

# Add project root to path
root = Path(__file__).resolve().parent.parent
sys.path.append(str(root))

from cognition.sophia.hephaestus import _get_store


def test_governance():
    print("=== Phase 1 Verification: Governance Sync ===")
    store = _get_store()
    rules = store.get_secure_rules("sophia")

    print(f"Total rules found in Axis 10: {len(rules)}")

    critical_rules = ["BA-01", "EMOJI_BAN", "PRIME_DIRECTIVE", "DB_FIRST"]
    found_critical = [r["id"] for r in rules if r["id"] in critical_rules]

    print(f"Critical rules detected: {found_critical}")

    if len(rules) >= 25:
        print("SUCCESS: Phase 1 Governance Sync verified.")
    else:
        print(f"FAILURE: Expected at least 25 rules, found {len(rules)}.")


if __name__ == "__main__":
    test_governance()
