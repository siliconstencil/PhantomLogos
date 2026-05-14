import asyncio
from typing import Any

from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)


async def anchor_inject_node(state: Any):
    """Managed Agents Node: Injects atomic anchors (codebase + skills) into context."""
    try:
        from cognition.mnemosyne.session_log import SessionLog
        from cognition.sophia.hephaestus import _get_mapper
        from src.architrave.context_cache import AnchorContextBuilder, ContextCacheStore

        from ..krisis import get_hermes_bridge_context

        builder = AnchorContextBuilder()
        mapper = _get_mapper()

        # Pillar 1: Injection-based context (Duzeltme 1)
        keywords = [w.strip(".,!?;:") for w in state["task"].split() if len(w) > 4]
        # suggest_context now uses SQL LIKE internally (Step 1.1)
        suggestions = await asyncio.to_thread(mapper.suggest_context, keywords)

        for sug in suggestions[:3]:
            builder.add_fragment(
                fragment_id=f"jit_{sug}",
                content=f"Module: {sug}\nRole: Project component (Spatial-Injected)",
                axis=5,
                precedence=120,
            )

        active_agent = state.get("active_agent", {})
        agent_id = active_agent.get("id") if isinstance(active_agent, dict) else None
        if agent_id:
            try:
                from src.clotho.skill_loader import get_skill_loader

                loader = get_skill_loader()
                matched = await asyncio.to_thread(loader.match_for_agent, agent_id)

                # AXIS 2/5: Jina Reranking for Skills
                try:
                    from src.muscle.reranker import JinaReranker

                    reranker = JinaReranker()
                    skill_texts = []
                    for m in matched:
                        ctx_test = await asyncio.to_thread(loader.get_context, m)
                        skill_texts.append(ctx_test or m)

                    reranked = await asyncio.to_thread(
                        reranker.rerank, state["task"], skill_texts, top_n=3
                    )
                    top_skills = []
                    if reranked and "results" in reranked:
                        for res in reranked["results"]:
                            idx = res["index"]
                            top_skills.append(matched[idx])
                    else:
                        top_skills = matched[:3]
                except Exception as e:
                    logger.warning(f"ergon: skill reranking failed ({e})")
                    top_skills = matched[:3]

                for sk_name in top_skills:
                    ctx = await asyncio.to_thread(loader.get_context, sk_name)
                    if ctx:
                        builder.add_fragment(
                            fragment_id=f"skill_{sk_name}", content=ctx, axis=8, precedence=130
                        )
            except Exception as e:
                logger.warning(f"ergon: skill context lookup failed ({e})")

        anchors_xml = builder.build_anchors_xml()
        hermes_facts = await asyncio.to_thread(get_hermes_bridge_context, state["session_id"])
        if hermes_facts:
            anchors_xml += hermes_facts

        if anchors_xml:
            try:
                cache = ContextCacheStore()
                cache.set(anchors_xml, ttl_seconds=3600)
            except Exception as e:
                logger.warning(f"ergon: anchor caching failed ({e})")

        memory_sync = False
        try:
            log = SessionLog(state["session_id"])
            memory_sync = log.wake()["status"] == "recovered"
        except Exception as e:
            logger.warning(f"ergon: session log wake failed ({e})")

        logger.info(f"ergon: Anchor injection complete (mem_sync={memory_sync})")
        return {"anchors": anchors_xml, "memory_sync": memory_sync}
    except asyncio.CancelledError:
        raise
    except Exception as e:
        logger.error(f"ergon: anchor_inject_node failed ({e})", exc_info=True)
        return {"anchors": "", "memory_sync": False}
