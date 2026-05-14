import asyncio
import sys
from pathlib import Path

import numpy as np

# Add project root to path
root = Path(__file__).resolve().parent.parent
sys.path.append(str(root))

from cognition.mnemosyne.semantic_store import SemanticStore
from src.architrave.model_registry import resolve_local_model
from src.utils.ollama_utils import get_ollama_client


async def seed_semantic():
    print("=== Phase 3.2: Semantic Seeding ===")

    fragments = [
        "Phantom Logos is a 3-tier agentic OS with L1 Strategist, L2 Runner, and L3 Auditor.",
        "Mnemosyne is the 14-axis memory architecture of Antigravity Sovereign OS.",
        "The BA-01 protocol mandates English for internals and Turkish for user interaction.",
        "EMOJI_BAN is a critical rule prohibiting any emoji usage in agent responses.",
        "Morpheus is the daemon responsible for model loading and VRAM management.",
        "Sovereign Gateway is the secure proxy for all external model communications.",
        "Axis 10 (Rational) stores governance rules and verified facts.",
        "Axis 5 (Spatial) maintains a graph representation of the codebase.",
        "Axis 8 (Meta-Cognition) tracks agent reliability and previous failures.",
        "Axis 6 (Semantic) uses LanceDB for vector-based long-term memory retrieval.",
        "The system uses Matryoshka 256 embeddings for high-performance search.",
        "Every strategic claim must cite its source using the [SRC:axis_N] format.",
        "A reliability score below 0.3 triggers a mandatory L0 approval lock.",
        "All file deletions must be preceded by a backup in .antigravity/backup/.",
        "Watchdog is the system daemon that monitors operational integrity and heartbeats.",
    ]

    try:
        client = get_ollama_client()
        embedding_model = resolve_local_model("embedding") or "nomic-embed-text:latest"

        print(f"Generating embeddings using {embedding_model}...")

        store = SemanticStore()

        for text in fragments:
            resp = await client.embeddings(model=embedding_model, prompt=text)
            # Matryoshka 256 slicing
            vec = np.array(resp.embedding)[:256]

            store.add_memories(
                texts=[text],
                vectors=[vec],
                metadata=[{"source": "seed", "importance": 0.8}],
                session_id="system",
            )
            print(f"  [Fragment] Indexed: {text[:40]}...")

        print("SUCCESS: Semantic seeding complete.")

    except Exception as e:
        print(f"Error during semantic seeding: {e}")


if __name__ == "__main__":
    asyncio.run(seed_semantic())
