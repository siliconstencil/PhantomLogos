import asyncio
from typing import Any
from src.utils.logging_config import setup_logger
from src.clotho.bootstrap import get_cpu_executor
from src.utils.ollama_utils import get_ollama_client

logger = setup_logger(__name__)

async def reflection_node(state: Any):
    """Axis 8: Reflective Insight Generation & Knowledge Extraction."""
    try:
        from cognition.mnemosyne.reflection_store import ReflectionStore
        store = ReflectionStore()
        session_id = state.get("session_id", "default")
        context = state.get("draft", "")
        for tr in (state.get("tool_results", []) or [])[-3:]:
            context += "\n" + str(tr.get("output", ""))[:2000]
            
        try:
            from src.architrave.entity_extractor import EntityExtractor
            extractor = EntityExtractor()
            
            # Phase 11.18.5: Use centralized CPU_HEAVY_EXECUTOR (max_workers=4) for GLiNER2
            loop = asyncio.get_running_loop()
            results = await loop.run_in_executor(get_cpu_executor(), extractor.extract_unified, context)
            
            await asyncio.to_thread(store.store_entities, session_id, results["entities"])
            await asyncio.to_thread(store.store_relations, session_id, results["relations"])
        except Exception as ee:
            logger.debug(f"ergon: Entity extraction skipped ({ee})")
            results = {"entities": [], "relations": []}
        
        critique = state.get("critique", {})
        score = critique.get("overall_score", 0) if isinstance(critique, dict) else 0
        insight = ""
        
        # Phase 11.19: Failure Memory Integration
        error = state.get("error")
        if (score > 0 and score < 0.5) or error:
            error_type = "logic_failure" if error is None else "runtime_error"
            flaws = critique.get("flaws", ["No specific flaws documented"])
            root_cause = str(error) if error else "; ".join(flaws)
            
            # Basic Prevention Rule Abstraction
            primary_flaw = flaws[0] if flaws else "Review task constraints more deeply"
            prevention_rule = f"To prevent {error_type}, the agent must: {primary_flaw}. [REF:Axis8]"
            
            if len(prevention_rule) >= 50:
                context_hash = store.store_failure(
                    error_type=error_type,
                    root_cause=root_cause,
                    prevention_rule=prevention_rule,
                    severity=2 if score < 0.3 else 1
                )
                if context_hash:
                    try:
                        from src.architrave.model_registry import get_embedding_model
                        model_name = get_embedding_model()
                        resp = await asyncio.wait_for(get_ollama_client().embeddings(model=model_name, prompt=state["task"]), timeout=15.0)
                        if resp:
                            vec = np.array(resp.embedding)[:256]
                            fm_store = FailureMemoryStore()
                            fm_store.add_failure_vector(
                                prevention_rule=prevention_rule,
                                vector=vec,
                                error_type=error_type,
                                context_hash=context_hash
                            )
                    except Exception as fe:
                        logger.debug(f"ergon: Semantic failure indexing failed ({fe})")

        if score >= 0.7:
            insight = f"Successful implementation of task: {state['task'][:100]}."
        elif state.get("tool_results"):
            insight = f"Tool execution learned {len(results['entities'])} entities."
            
        if insight: store.store_reflection(session_id, insight, category="automatic")
        return {"reflection_insight": insight, "memory_sync": True}
    except Exception as e:
        logger.warning(f"ergon: reflection_node failed ({e})")
        return {"reflection_insight": None, "memory_sync": False}
