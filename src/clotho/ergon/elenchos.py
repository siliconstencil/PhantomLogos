import asyncio
import os
from typing import Any

from src.utils.logging_config import setup_logger

from .koinonia import record_step

logger = setup_logger(__name__)


async def critique_node(state: Any) -> dict[str, Any]:
    session_id = state.get("session_id", "default")
    agent_id = state.get("active_agent", "sophia")
    draft = state.get("draft", "")
    contract = state.get("contract", {"threshold": 0.7})
    tool_results = state.get("tool_results", [])

    logger.info(f"ergon: Starting 3-Pass L3 Verification for {agent_id} in {session_id}")

    try:
        from src.lachesis import AdversarialEvaluator

        evaluator = AdversarialEvaluator(session_id)

        anchor_path = "data/ankyra_anchor.md"
        anchors = ""
        if await asyncio.to_thread(os.path.exists, anchor_path):
            from pathlib import Path

            anchors = await asyncio.to_thread(Path(anchor_path).read_text, "utf-8")

        # Pass 1: Heuristic (Stateless, 0 VRAM)
        result = await evaluator.evaluate(
            draft, contract=contract, tool_results=tool_results, anchors=anchors
        )
        zone = result.get("zone", "ambiguous")
        overall_score = result.get("overall_score", 0.0)

        final_critique = result

        if zone == "ambiguous":
            # Pass 2: Light LLM (Phi-4 Mini)
            logger.info("ergon: Ambiguous zone detected. Launching Pass 2 (Phi-4 Mini)...")
            from cognition.sophia.sophia import run_critique

            critique_res = await run_critique(draft, session_id=session_id)

            final_critique = critique_res.model_dump()
            final_critique["overall_score"] = overall_score
            final_critique["zone"] = "yellow"

            # Pass 3: Heavy LLM (Qwen-7b)
            if critique_res.confidence_score < 0.6:
                logger.warning(
                    f"ergon: Pass 2 confidence low ({critique_res.confidence_score}). Launching Pass 3 (Heavy logic override)..."
                )

                # Morpheus: Mandatory Flush (Phi-4 2.8GB + Qwen 4.7GB > 7.0GB usable)
                from cognition.morpheus.loader import ModelLoader

                await asyncio.to_thread(ModelLoader().flush)
                logger.info("ergon: VRAM flushed for Pass 3 transition.")

                from src.architrave.model_registry import resolve_local_model

                expert_model = resolve_local_model("critique", "fallback")

                heavy_res = await run_critique(
                    draft, session_id=session_id, model_name=expert_model
                )
                final_critique = heavy_res.model_dump()
                final_critique["overall_score"] = overall_score
                final_critique["zone"] = "heavy_review"

        # Meta-Cognition Axis 8 Update
        try:
            from cognition.mnemosyne.meta_cognition import MetaCognitionStore

            meta = MetaCognitionStore()
            # EWMA Model Transition: Pass overall_score directly as current_score
            meta.adjust_reliability(
                agent_id=agent_id,
                delta=overall_score,
                violation_type="low_critique_score" if overall_score < 0.5 else "",
                session_id=session_id,
            )
            meta.record(
                agent_id=agent_id,
                score=overall_score,
                flaws=final_critique.get("flaws", []),
                session_id=session_id,
            )
        except Exception as e_meta:
            logger.error(f"ergon: Metacognition update failed ({e_meta})")

        # Map 'is_valid' to 'is_pass' for krisis consistency
        final_critique["is_pass"] = final_critique.get(
            "is_valid", final_critique.get("is_pass", False)
        )

        # Centralized Mnemosyne Hypergraph edge addition
        try:
            from cognition.mnemosyne.hypergraph_models import Hyperedge, HypernodeRef
            from cognition.mnemosyne.hypergraph_store import HypergraphStore

            nodes = [
                HypernodeRef(
                    axis_id=8,
                    entity_type="meta_cognition",
                    entity_key=agent_id,
                    label=f"Meta: {agent_id}",
                ),
                HypernodeRef(
                    axis_id=3,
                    entity_type="goals",
                    entity_key=session_id,
                    label=f"Goal: {session_id}",
                ),
                HypernodeRef(
                    axis_id=6,
                    entity_type="entity",
                    entity_key=final_critique.get("zone", "yellow"),
                    label=f"Critique Zone: {final_critique.get('zone')}",
                ),
            ]
            edge = Hyperedge(nodes=nodes, relation_type="critique_outcome", weight=overall_score)
            HypergraphStore().add_edge(edge)
            logger.info(
                f"HypergraphStore: Added critique hyperedge {edge.edge_id} connecting Axes 8, 3, 6."
            )
        except Exception as e_hg:
            logger.warning(f"ergon: Hypergraph update failed in critique_node ({e_hg})")

        # [Step 3] Centralized Knowledge Extraction (Axis 8)
        try:
            from src.architrave.entity_extractor import EntityExtractor

            await asyncio.to_thread(EntityExtractor.harvest_knowledge, draft, session_id)
        except Exception as e_ext:
            logger.warning(f"ergon: Knowledge extraction failed in critique_node ({e_ext})")

        await asyncio.to_thread(record_step, state, "critique")
        return {"critique": final_critique, "memory_sync": True}

    except asyncio.CancelledError:
        raise
    except Exception as e:
        logger.error(f"ergon: critique_node failed ({e})", exc_info=True)
        # Emergency VRAM Flush on failure to prevent hang
        try:
            from cognition.morpheus.loader import ModelLoader

            await asyncio.to_thread(ModelLoader().flush)
        except Exception as e:
            logger.debug(f"ergon: VRAM flush skipped ({e})")
        return {
            "critique": {"is_pass": False, "overall_score": 0, "zone": "red", "flaws": [str(e)]},
            "memory_sync": False,
        }
