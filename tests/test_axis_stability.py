import asyncio
import os
from datetime import datetime

import pytest

from src.utils.logging_config import setup_logger

logger = setup_logger("axis_test")


@pytest.mark.asyncio
async def test_axis_stability():
    print(f"--- Phantom Logos 14-Axis Stability Audit ({datetime.now().isoformat()}) ---")

    results = {}

    # 1. Axis 1: Episodic (Session History)
    try:
        from cognition.mnemosyne.episodic_store import EpisodicStore

        store = EpisodicStore()
        store.log("test_session", "stability_test", detail="Verifying Axis 1", outcome="success")
        results["Axis 1 (Episodic)"] = "PASS"
    except Exception as e:
        results["Axis 1 (Episodic)"] = f"FAIL ({e})"

    # 2. Axis 2: Procedural (Tool Tracking)
    try:
        from cognition.mnemosyne.procedural_store import ProceduralStore

        store = ProceduralStore()
        store.record_usage("axis_test_tool", "diagnostic", True, 100)
        results["Axis 2 (Procedural)"] = "PASS"
    except Exception as e:
        results["Axis 2 (Procedural)"] = f"FAIL ({e})"

    # 3. Axis 3: Goals (Objectives)
    try:
        from cognition.mnemosyne.goal_store import GoalStore

        store = GoalStore()
        store.add("Diagnostic Test", "Verify axis stability", 1)
        results["Axis 3 (Goals)"] = "PASS"
    except Exception as e:
        results["Axis 3 (Goals)"] = f"FAIL ({e})"

    # 4. Axis 4: Temporal (Metrics/Time-series)
    try:
        from cognition.mnemosyne.temporal_store import TemporalStore

        store = TemporalStore()
        store.record(session_id="test_session", event_type="stability_check", latency_ms=10.0)
        results["Axis 4 (Temporal)"] = "PASS"
    except Exception as e:
        results["Axis 4 (Temporal)"] = f"FAIL ({e})"

    # 5. Axis 5: Spatial (Dependency Graph)
    try:
        from cognition.mnemosyne.spatial_store import SpatialStore
        from src.lachesis.mapper import CodebaseMapper

        mapper = CodebaseMapper(project_path=os.getcwd(), spatial_store=SpatialStore())
        # Test suggest_context
        mapper.suggest_context(["sophia", "gnosis"])
        results["Axis 5 (Spatial)"] = "PASS"
    except Exception as e:
        results["Axis 5 (Spatial)"] = f"FAIL ({e})"

    # 6. Axis 6: Semantic (LanceDB/Vector)
    try:
        import numpy as np

        from cognition.mnemosyne.semantic_store import SemanticStore

        store = SemanticStore()
        store.add_memories(
            ["Axis Test Fragment"],
            [np.zeros(256)],
            [{"axis": "test", "importance": 0.9, "timestamp": 0.0}],
        )
        results["Axis 6 (Semantic)"] = "PASS"
    except Exception as e:
        results["Axis 6 (Semantic)"] = f"FAIL ({e})"

    # 7. Axis 7: Operational (Telemetry/Logs)
    try:
        from cognition.mnemosyne.operational_store import OperationalStore

        store = OperationalStore()
        store.record_event(name="stability.check", level="INFO", message="Axis 7 OK")
        results["Axis 7 (Operational)"] = "PASS"
    except Exception as e:
        results["Axis 7 (Operational)"] = f"FAIL ({e})"

    # 8. Axis 8: Meta-Cognition (Reliability)
    try:
        from cognition.mnemosyne.meta_cognition import MetaCognitionStore

        store = MetaCognitionStore()
        store.get_reliability("sophia")
        results["Axis 8 (Meta-Cog)"] = "PASS"
    except Exception as e:
        results["Axis 8 (Meta-Cog)"] = f"FAIL ({e})"

    # 9. Axis 9: Creative/Tone (Style)
    try:
        from cognition.mnemosyne.tone_store import ToneStore

        store = ToneStore()
        store.record_tone("test_session", "Professional diagnostic mode.")
        results["Axis 9 (Tone)"] = "PASS"
    except Exception as e:
        results["Axis 9 (Tone)"] = f"FAIL ({e})"

    # 10. Axis 10: Rational (Rules/Facts)
    try:
        from cognition.mnemosyne.rational_store import MnemosyneRationalStore

        store = MnemosyneRationalStore()
        store.get_secure_rules("sophia")
        results["Axis 10 (Rational)"] = "PASS"
    except Exception as e:
        results["Axis 10 (Rational)"] = f"FAIL ({e})"

    # 11. Axis 11: Verification (Formal/Math)
    try:
        from src.lachesis.verifiers import SympyVerifier

        verifier = SympyVerifier()
        res = verifier.verify_expression("x**2 - 1", "(x-1)*(x+1)")
        results["Axis 11 (Verification)"] = "PASS" if res["is_valid"] else "FAIL"
    except Exception as e:
        results["Axis 11 (Verification)"] = f"FAIL ({e})"

    # 12. Axis 12: Efficiency (Context/Cache)
    try:
        from src.architrave.context_cache import ContextCacheStore

        store = ContextCacheStore()
        store.set("stability_test_anchor", ttl_seconds=60)
        results["Axis 12 (Efficiency)"] = "PASS"
    except Exception as e:
        results["Axis 12 (Efficiency)"] = f"FAIL ({e})"

    # 13. Axis 13: Cross-Session Patterns (OpenCode)
    try:
        from src.architrave.opencode_store import OpenCodeStore

        store = OpenCodeStore()
        store.get_cross_session_patterns()
        results["Axis 13 (Patterns)"] = "PASS"
    except Exception as e:
        results["Axis 13 (Patterns)"] = f"FAIL ({e})"

    # 14. Axis 14: Visual (VLM History)
    try:
        from cognition.mnemosyne.visual_store import VisualStore

        store = VisualStore()
        await store.store_vision(
            "test_session", "stability_test.png", "A diagnostic image.", "Thinking mode."
        )
        results["Axis 14 (Visual)"] = "PASS"
    except Exception as e:
        results["Axis 14 (Visual)"] = f"FAIL ({e})"

    print("\n--- FINAL AUDIT RESULTS ---")
    for axis, status in results.items():
        print(f"{axis}: {status}")

    score = sum(1 for s in results.values() if s == "PASS")
    print(f"\nFinal Stability Score: {score}/14")


if __name__ == "__main__":
    asyncio.run(test_axis_stability())
