import asyncio
import re
from typing import Any, List, Dict
from src.utils.logging_config import setup_logger
from src.utils.ollama_utils import get_ollama_client

logger = setup_logger(__name__)

async def _semantic(bridge, input_data):
    try:
        import numpy as np
        from cognition.mnemosyne.semantic_store import SemanticStore
        query = input_data.get("query", "") if isinstance(input_data, dict) else str(input_data)
        limit = input_data.get("limit", 5) if isinstance(input_data, dict) else 5
        model_name = bridge._resolve_model("embedding")
        resp = await get_ollama_client().embeddings(model=model_name, prompt=query)
        vec = np.array(resp["embedding"])
        store = SemanticStore()
        candidates = store.search(vec, session_id=bridge.session_id, limit=100, mode="hybrid", query_text=query)
        if not candidates: return []
        rerank_data = await asyncio.to_thread(_rerank_results, query, candidates[:20])
        reranked = rerank_data.get("results", [])
        warning = rerank_data.get("integrity_warning")
        if warning:
            try:
                from cognition.mnemosyne.operational_store import OperationalStore
                OperationalStore().record_event(name="semantic.integrity_warning", level="WARNING", message=f"Retrieval integrity compromised: {warning}", agent_id=bridge.session_id[:12])
            except: pass
            return {"results": reranked[:limit], "integrity_warning": warning, "status": "degraded"}
        return reranked[:limit]
    except Exception as e:
        logger.error(f"ToolBridge: Semantic search failed ({e})")
        return f"Semantic search error: {str(e)}"

async def _skill(bridge, input_data):
    try:
        from src.clotho.skill_loader import get_skill_loader
        loader = get_skill_loader()
        if isinstance(input_data, dict):
            skill_name = input_data.get("name", "")
            if input_data.get("action") == "match":
                return await asyncio.to_thread(loader.match_for_task, input_data.get("task", ""))
            return await asyncio.to_thread(loader.get_context, skill_name) or f"Skill '{skill_name}' not found"
        if isinstance(input_data, str) and input_data == "list":
            return await asyncio.to_thread(loader.list_skills)
        return await asyncio.to_thread(loader.get_context, str(input_data)) or f"Skill '{input_data}' not found"
    except Exception as e:
        return f"Skill loader error: {str(e)}"

async def _mapper(bridge, input_data):
    return {
        "status": "deprecated",
        "message": "Spatial context is now auto-injected via anchor_inject_node.",
        "hint": "Use state['spatial_context'] instead of calling mapper tool. This saves tokens and is more accurate."
    }

async def _prune(bridge, input_data):
    try:
        from src.atropos.context_pruner import ContextPruner
        pruner = ContextPruner()
        tier = input_data.get("tier", "reasoning") if isinstance(input_data, dict) else "reasoning"
        text = input_data.get("text", "") if isinstance(input_data, dict) else str(input_data)
        return await asyncio.to_thread(pruner.slice_context_window, text, tier)
    except Exception as e:
        return f"Pruner error: {str(e)}"

def _rerank_results(query: str, candidates: List[Dict]) -> Dict[str, Any]:
    if not candidates: return {"results": [], "integrity_warning": None}
    try:
        from src.muscle.reranker import JinaReranker
        reranker = JinaReranker()
        texts = [doc.get("text", "") for doc in candidates]
        results = reranker.rerank(query, texts, top_n=len(candidates))
        reranked_docs = []
        for res in results.get("results", []):
            idx = res["index"]
            if idx < len(candidates):
                doc = candidates[idx].copy()
                doc["rerank_score"] = res["score"]
                reranked_docs.append(doc)
        return {"results": reranked_docs, "integrity_warning": results.get("integrity_warning")}
    except Exception as e:
        logger.warning(f"ToolBridge: Jina Reranking failed ({e}), using heuristic fallback")
        query_words = set(re.findall(r"\w+", query.lower()))
        if not query_words: return {"results": candidates, "integrity_warning": str(e)}
        scored_results = []
        for doc in candidates:
            text = doc.get("text", "").lower()
            doc_words = set(re.findall(r"\w+", text))
            overlap = len(query_words.intersection(doc_words))
            score = overlap / len(query_words)
            scored_results.append((score, doc))
        scored_results.sort(key=lambda x: x[0], reverse=True)
        return {"results": [item[1] for item in scored_results], "integrity_warning": f"Heuristic fallback active: {str(e)}"}
