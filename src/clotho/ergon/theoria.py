import asyncio
from typing import Any

import numpy as np

from cognition.sophia.hephaestus import _get_failure_memory, _get_reflection, _get_semantic
from src.architrave.model_registry import resolve_local_model
from src.clotho.bootstrap import get_cpu_executor
from src.utils.logging_config import setup_logger
from src.utils.ollama_utils import get_ollama_client

logger = setup_logger(__name__)


async def extract_reflection_llm(state: Any) -> str:
    """[SRC:axis_8] Uses Sophia to extract high-level technical insights from recent steps."""
    try:
        task = state.get("task", "unknown")
        context = state.get("draft", "")
        for tr in (state.get("tool_results", []) or [])[-3:]:
            context += "\n" + str(tr.get("output", ""))[:1500]

        prompt = f"""Review the following task and execution results.
Identify 1-2 critical technical insights or lessons learned to prevent future errors or improve efficiency.
Task: {task}
Context: {context}

Instruction: Provide ONLY the technical insight as a concise sentence. Do NOT include greetings or filler.
Insight:"""

        client = get_ollama_client()
        # [TIER 3.2 FIX] Use dynamic registry instead of hardcoded string [HH:MM AM/PM PT]
        critique_model = resolve_local_model("critique", "primary")
        resp = await client.generate(model=critique_model, prompt=prompt)
        insight = resp.response.strip()
        return insight if len(insight) > 10 else ""
    except Exception as e:
        logger.debug(f"theoria: LLM reflection extraction failed ({e})")
        return ""


async def reflection_node(state: Any):
    """Axis 8: Reflective Insight Generation & Knowledge Extraction."""
    try:
        store = _get_reflection()  # Singleton Alignment (B5)
        session_id = state.get("session_id", "default")
        context = state.get("draft", "")
        for tr in (state.get("tool_results", []) or [])[-3:]:
            context += "\n" + str(tr.get("output", ""))[:2000]

        try:
            from src.architrave.entity_extractor import EntityExtractor

            extractor = EntityExtractor()

            # Phase 11.18.5: Use centralized CPU_HEAVY_EXECUTOR
            loop = asyncio.get_running_loop()
            results = await loop.run_in_executor(
                get_cpu_executor(), extractor.extract_unified, context
            )

            logger.info(
                f"theoria: GLiNER2 found {len(results.get('entities', []))} entities and {len(results.get('relations', []))} relations."
            )

            # Phase 1.0.2: Deep Path Fallback if GLiNER2 fails to find relations
            if not results.get("relations") and results.get("entities"):
                logger.info("theoria: Triggering Deep Path fallback (Ollama)...")
                results["relations"] = await extractor.extract_relations_batch(
                    context, results["entities"]
                )
                logger.info(f"theoria: Deep Path found {len(results['relations'])} relations.")

            await asyncio.to_thread(store.store_entities, session_id, results["entities"])
            await asyncio.to_thread(store.store_relations, session_id, results["relations"])
        except Exception as ee:
            logger.warning(
                f"theoria: GLiNER2 extraction failed ({ee}). Triggering full Deep Path fallback..."
            )
            try:
                # Fallback: Try to get relations via Ollama if unified extractor fails
                entities = results.get("entities", [])
                fallback_relations = await extractor.extract_relations_batch(context, entities)
                results = {"entities": entities, "relations": fallback_relations}

                await asyncio.to_thread(store.store_entities, session_id, results["entities"])
                await asyncio.to_thread(store.store_relations, session_id, results["relations"])
                logger.info(
                    f"theoria: Deep Path recovery successful. Found {len(fallback_relations)} relations."
                )
            except Exception as fe:
                logger.error(f"theoria: Knowledge extraction failed entirely ({fe})")
                results = {"entities": [], "relations": []}

        critique = state.get("critique", {})
        score = critique.get("overall_score", 0) if isinstance(critique, dict) else 0
        insight = ""

        # Phase 11.19: Failure Memory Integration (B1, B2, B3)
        error = state.get("error")
        if (score > 0 and score < 0.5) or error:
            error_type = "logic_failure" if error is None else "runtime_error"
            flaws = critique.get("flaws", ["No specific flaws documented"])
            root_cause = str(error) if error else "; ".join(flaws)

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
                    model_name = resolve_local_model("embedding")
                    resp = await asyncio.wait_for(
                        get_ollama_client().embeddings(model=model_name, prompt=state["task"]),
                        timeout=15.0,
                    )
                    if resp:
                        # B14: Matryoshka 256 slicing
                        vec = np.array(resp.embedding)[:256]
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
            store.store_reflection(session_id, insight, category="automatic")
            # Mirror to LanceDB for semantic search (P5/M6)
            try:
                model_name = resolve_local_model("embedding")
                try:
                    resp = await asyncio.wait_for(
                        get_ollama_client().embeddings(model=model_name, prompt=insight),
                        timeout=10.0,
                    )
                    vec = np.array(resp.embedding)[:256]
                except Exception as ee:
                    logger.warning(f"theoria: Embedding generation failed ({ee}), using fallback.")
                    vec = np.zeros(256)

                _get_semantic().add_memories(
                    texts=[insight],
                    vectors=[vec],
                    metadata=[{"axis": "reflection", "category": "automatic"}],
                    session_id=session_id,
                )
            except Exception as e:
                logger.warning(f"theoria: Semantic mirroring failed ({e})")

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
            logger.warning(f"theoria: Failed to log episodic/experience write ({le})")

        return {"reflection_insight": insight, "memory_sync": True}
    except Exception as e:
        logger.warning(f"theoria: reflection_node failed ({e})")
        return {"reflection_insight": None, "memory_sync": False}
