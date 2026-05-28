import asyncio

import numpy as np

from cognition.sophia.hephaestus import _get_failure_memory, _get_reflection, _get_semantic
from src.architrave.model_registry import resolve_local_model
from src.architrave.otl_engine import get_otl_engine
from src.clotho.bootstrap import get_cpu_executor
from src.utils.logging_config import setup_logger
from src.utils.ollama_utils import get_ollama_client

from .koinonia import record_step

logger = setup_logger(__name__)


async def extract_reflection_llm(state: dict) -> str:
    """[SRC:axis_8] Uses Sophia to extract high-level technical insights from recent steps."""
    try:
        task = state.get("task", "unknown")
        context = state.get("draft", "")
        for tr in (state.get("tool_results", []) or [])[-3:]:
            context += "\n" + str(tr.get("output", ""))[:1500]

        prompt = f"""Review the following task and execution results.
Identify one to two critical technical insights or lessons learned to prevent future errors or improve efficiency.
Task: {task}
Context: {context}

Instruction: Provide ONLY the technical insight as a concise sentence. Do NOT include greetings or filler.
Insight:"""

        client = get_ollama_client()
        # [TIER 3.2 FIX] Use dynamic registry instead of hardcoded string [HH:MM AM/PM PT]
        critique_model = resolve_local_model("critique", "primary")
        resp = await asyncio.wait_for(
            client.generate(model=critique_model, prompt=prompt), timeout=30.0
        )
        insight = (resp.response or "").strip()
        return insight if len(insight) > 10 else ""
    except Exception as e:
        logger.debug("theoria: LLM reflection extraction failed (%s)", e)
        return ""


async def reflection_node(state: dict) -> dict:
    """Axis 8: Reflective Insight Generation & Knowledge Extraction."""
    try:
        store = _get_reflection()  # Singleton Alignment (B5)
        session_id = state.get("session_id", "default")
        context = state.get("draft", "")
        for tr in (state.get("tool_results", []) or [])[-3:]:
            context += "\n" + str(tr.get("output", ""))[:2000]

        # Initialize to safe defaults before try block to prevent UnboundLocalError
        results: dict = {"entities": [], "relations": []}
        extractor = None

        try:
            from src.architrave.entity_extractor import EntityExtractor

            extractor = EntityExtractor()

            # Phase 11.18.5: Use centralized CPU_HEAVY_EXECUTOR
            loop = asyncio.get_running_loop()
            results = await loop.run_in_executor(
                get_cpu_executor(), extractor.extract_unified, context
            )

            logger.info(
                "theoria: GLiNER2 found %d entities and %d relations.",
                len(results.get("entities", [])),
                len(results.get("relations", [])),
            )

            # Phase 1.0.2: Deep Path Fallback only if GLiNER2 finds entities but no relations
            if not results.get("relations") and results.get("entities"):
                logger.info("theoria: Triggering Deep Path fallback (Ollama)...")
                results["relations"] = await extractor.extract_relations_batch(
                    context, results["entities"]
                )
                logger.info("theoria: Deep Path found %d relations.", len(results["relations"]))

            await asyncio.to_thread(store.store_entities, session_id, results["entities"])
            await asyncio.to_thread(store.store_relations, session_id, results["relations"])
        except Exception as ee:
            logger.warning("theoria: GLiNER2 extraction failed (%s). Skipping knowledge store.", ee)
            # results is already safe default: {"entities": [], "relations": []}
            # No fallback loop - extractor may be in broken state, skip persistence.

        critique = state.get("critique", {})
        score = critique.get("overall_score", 0) if isinstance(critique, dict) else 0
        insight = ""

        if isinstance(state, dict) and state.get("trajectory_id"):
            try:
                otl = get_otl_engine()
                model_tier = state.get("selected_model_tier", "primary")
                reward = (score - 0.5) * 2.0
                otl.update_weight(
                    "draft" if model_tier != "expert" else "expert_draft", model_tier, reward
                )
            except Exception as e:
                logger.debug("theoria: OTL feedback failed (%s)", e)

        # Phase 11.19: Failure Memory Integration (B1, B2, B3)
        error = state.get("error")
        if (score > 0 and score < 0.5) or error:
            error_type = "logic_failure" if error is None else "runtime_error"
            flaws = critique.get("flaws", ["No specific flaws documented"])
            root_cause = str(error) if error else "; ".join([str(f) for f in flaws if f])

            primary_flaw = flaws[0] if flaws else "Review task constraints more deeply"
            prevention_rule = (
                f"To prevent {error_type}, the agent must: {primary_flaw}. [REF:Axis8]"
            )

            if len(prevention_rule) >= 50:
                context_hash = store.store_failure(
                    error_type=error_type,
                    root_cause=root_cause,
                    prevention_rule=prevention_rule,
                    severity=2 if score < 0.3 else 1,
                )
                if context_hash:
                    # B3: Exposing embedding errors (removed masking try/except)
                    import os

                    from src.architrave.mcp import get_slm_client

                    slm = get_slm_client()
                    resp_embedding = []
                    if os.getenv("SLM_ENABLED", "true").lower() == "true" and slm.health():
                        try:
                            resp_embedding = await slm.aembed(state["task"])
                        except Exception as e:
                            logger.error(
                                "theoria: SLM embedding failed (%s). Falling back to local Ollama.",
                                e,
                            )

                    if not resp_embedding:
                        model_name = resolve_local_model("embedding")
                        resp = await asyncio.wait_for(
                            get_ollama_client().embeddings(model=model_name, prompt=state["task"]),
                            timeout=15.0,
                        )
                        resp_embedding = resp.embedding if resp else []

                    if resp_embedding:
                        # B14: Matryoshka 256 slicing
                        vec = np.array(resp_embedding)[:256]

                        fm_store = _get_failure_memory()
                        fm_store.add_failure_vector(
                            prevention_rule=prevention_rule,
                            vector=vec,
                            error_type=error_type,
                            context_hash=context_hash,
                        )

        # P2: LLM Reflection Loop (Sophia'ya sor)
        if score >= 0.7 or state.get("tool_results"):
            insight = await extract_reflection_llm(state)

        if not insight:
            if score >= 0.7:
                insight = f"Successful implementation of task: {state['task'][:100]}."
            elif state.get("tool_results"):
                insight = f"Tool execution learned {len(results['entities'])} entities."

        if insight:
            store.store_reflection(session_id, insight, category="automatic", importance=0.7)

            # Mnemosyne Hypergraph edge addition
            try:
                import hashlib

                from cognition.mnemosyne.hypergraph_models import Hyperedge, HypernodeRef
                from cognition.mnemosyne.hypergraph_store import HypergraphStore

                insight_key = hashlib.sha256(insight.encode()).hexdigest()[:8]
                nodes = [
                    HypernodeRef(
                        axis_id=8,
                        entity_type="reflection",
                        entity_key=insight_key,
                        label=f"Insight: {insight[:30]}...",
                    ),
                    HypernodeRef(
                        axis_id=6,
                        entity_type="semantic",
                        entity_key=session_id,
                        label=f"Semantic Ref: {session_id}",
                    ),
                    HypernodeRef(
                        axis_id=4,
                        entity_type="temporal",
                        entity_key=session_id,
                        label=f"Session Time: {session_id}",
                    ),
                ]
                edge = Hyperedge(nodes=nodes, relation_type="generated_reflection", weight=0.7)
                HypergraphStore().add_edge(edge)
                logger.info(
                    f"HypergraphStore: Added reflection hyperedge {edge.edge_id} connecting Axes 8, 6, 4."
                )
            except Exception as e_hg:
                logger.warning("theoria: Hypergraph update failed in store_reflection (%s)", e_hg)

            # Mirror to LanceDB for semantic search (P5/M6)
            try:
                from src.utils.service_locator import get_matryoshka

                matryoshka = get_matryoshka()
                try:
                    vec = await matryoshka.embed_document(insight)
                except Exception as ee:
                    logger.warning("theoria: Matryoshka embedding failed (%s), using fallback.", ee)
                    vec = np.zeros(256)

                _get_semantic().add_memories(
                    texts=[insight],
                    vectors=[vec],
                    metadata=[{"axis": "reflection", "category": "automatic"}],
                    session_id=session_id,
                )
            except Exception as e:
                logger.warning("theoria: Semantic mirroring failed (%s)", e)

        # SLM Observe: Register cognitive reflection as observation
        if insight:
            try:
                from src.architrave.mcp import get_slm_client

                slm = get_slm_client()
                await slm.aobserve(content=insight, agent_id="sophia")
            except Exception as e:
                logger.debug("theoria: SLM observe failed (%s)", e)

        # Phase 2.4: Episodic Write Path Activation
        try:
            from cognition.sophia.hephaestus import _get_episodic

            _get_episodic().log(
                session_id=session_id,
                agent_id="clotho",
                action="session_reflection",
                detail=f"Insight: {insight[:100]}... Score: {score}",
                outcome="success" if score >= 0.7 else "degraded",
            )
            # [Phase 1.0.21] Meta-Cognition (Axis 8) Restoration
            from cognition.mnemosyne.meta_cognition import MetaCognitionStore

            MetaCognitionStore().record_experience(
                agent_id="sophia",
                session_id=session_id,
                task_pattern="general",
                success=(score >= 0.7),
                quality=score,
            )
        except Exception as le:
            logger.warning("theoria: Failed to log episodic/experience write (%s)", le)

        await asyncio.to_thread(record_step, state, "reflection")
        return {"reflection_insight": insight, "memory_sync": True}
    except Exception as e:
        logger.warning("theoria: reflection_node failed (%s)", e)
        return {"reflection_insight": None, "memory_sync": False}
