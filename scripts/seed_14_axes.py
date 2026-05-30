"""Seed 14 Mnemosyne axes with baseline data for health check."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np

from cognition.mnemosyne.models import VisualMemory
from cognition.mnemosyne.operational_store import OperationalStore
from cognition.mnemosyne.tone_store import ToneStore
from cognition.mnemosyne.visual_store import VisualStore
from cognition.sophia.hephaestus import (
    get_episodic,
    get_goals,
    get_meta,
    get_procedural,
    get_reflection,
    get_semantic,
    get_spatial,
    get_store,
    get_temporal,
)


def seed_all():
    session_id = "seed_14_axes"
    print("Seeding 14 Mnemosyne axes...")

    # Axis 1: Episodic
    get_episodic().log(session_id=session_id, action="seed_14_axes")
    print("  Axis 1 (Episodic): seeded")

    # Axis 2: Procedural
    get_procedural().record_usage(tool_name="seed", task_type="seed", success=True)
    print("  Axis 2 (Procedural): seeded")

    # Axis 3: Goals
    get_goals().add(title="Seed Goal", description="Baseline seed", session_id=session_id)
    print("  Axis 3 (Goals): seeded")

    # Axis 4: Temporal
    get_temporal().record(session_id=session_id, event_type="seed")
    print("  Axis 4 (Temporal): seeded")

    # Axis 5: Spatial
    get_spatial().record_dependency(source="seed_module", target="seed_module")
    print("  Axis 5 (Spatial): seeded")

    # Axis 6: Semantic
    vec = np.zeros(256, dtype=np.float32)
    get_semantic().add_memories(
        texts=["System seed baseline integrity check data for health check audit."],
        vectors=[vec],
        metadata=[{"seed": True}],
        session_id=session_id,
    )
    print("  Axis 6 (Semantic): seeded")

    # Axis 7: Operational
    OperationalStore().record_event(
        name="seed", level="INFO", message="Seed baseline", session_id=session_id
    )
    print("  Axis 7 (Operational): seeded")

    # Axis 8: Meta
    get_meta().adjust_reliability(agent_id="seed", delta=0.5, session_id=session_id)
    print("  Axis 8 (Meta): seeded")

    # Axis 9: Tone
    ToneStore().record_tone(session_id=session_id, message="Seed baseline tone")
    print("  Axis 9 (Tone): seeded")

    # Axis 10: Rational
    get_store().add_fact(subject="seed_fact", obj="baseline", agent_id=session_id)
    print("  Axis 10 (Rational): seeded")

    # Axis 11: Verify
    get_reflection().store_reflection(session_id=session_id, insight="Seed verification baseline.")
    print("  Axis 11 (Verify): seeded")

    # Axis 12: Cache - populated at runtime
    print("  Axis 12 (Cache): skip - populated at runtime")

    # Axis 13: Patterns - populated by Hermes
    print("  Axis 13 (Patterns): skip - populated by Hermes CLI")

    # Axis 14: Visual
    vs = VisualStore()
    session = vs.Session()
    try:
        memory = VisualMemory(
            image_hash="seed",
            description="Seed baseline visual memory",
            source_path="seed_14_axes",
            variant="seed",
            metadata_json='{"seed": true, "axis": 14}',
            session_id=session_id,
        )
        session.add(memory)
        session.commit()
        print("  Axis 14 (Visual): seeded")
    except Exception as e:
        print(f"  Axis 14 (Visual): FAILED - {e}")
        session.rollback()
    finally:
        session.close()

    print("\nAll seed operations completed.")


if __name__ == "__main__":
    seed_all()
