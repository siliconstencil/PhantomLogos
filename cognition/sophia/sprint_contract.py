import re
import asyncio
from typing import List, Dict, Any
from src.utils.logging_config import setup_logger
from src.utils.ollama_utils import get_ollama_client
from cognition.mnemosyne.session_log import SessionLog

logger = setup_logger(__name__)

TASK_COMPLEXITY_KEYWORDS = {
    "refactor": 0.9,
    "migrate": 0.85,
    "implement": 0.8,
    "create": 0.8,
    "build": 0.85,
    "design": 0.85,
    "fix": 0.6,
    "update": 0.5,
    "add": 0.55,
    "remove": 0.4,
    "test": 0.6,
    "optimize": 0.75,
    "deploy": 0.7,
    "document": 0.4,
    "api": 0.8,
    "database": 0.8,
    "auth": 0.9,
    "security": 0.95,
}

class SprintContract:
    """
    SOTA 2026 Sprint Contract.
    Negotiates the 'Definition of Done' between Sophia, Clotho, and Lachesis.
    Task complexity is derived from keyword analysis of the task description.
    """
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.log = SessionLog(session_id)

    _keyword_embeddings = None

    @classmethod
    async def _load_keyword_embeddings(cls):
        """Pre-compute and cache all keyword embeddings (once per process)."""
        if cls._keyword_embeddings is not None:
            return cls._keyword_embeddings
        import ollama, numpy as np
        from src.clotho.activity import ActivityMonitor
        ActivityMonitor().increment()
        from src.architrave.model_registry import get_embedding_model
        model_name = get_embedding_model()
        client = get_ollama_client()
        try:
            emb = {}
            for kw in TASK_COMPLEXITY_KEYWORDS:
                try:
                    resp = await asyncio.wait_for(client.embeddings(model=model_name, prompt=kw), timeout=20.0)
                    emb[kw] = np.array(resp.embedding[:256])
                except Exception as e:
                    logger.warning(f"SprintContract: Failed to load embedding for keyword '{kw}' ({e})")
        finally:
            ActivityMonitor().decrement()
        cls._keyword_embeddings = emb
        logger.info(f"SprintContract: Cached {len(emb)} keyword embeddings ({model_name}, 256-dim)")
        return emb

    async def _embedding_complexity(self, task: str) -> float:
        """Fallback: nomic-embed-text-v2-moe-q8 embedding + cosine similarity with cached keywords."""
        import ollama, numpy as np
        from src.clotho.activity import ActivityMonitor
        from src.architrave.model_registry import get_embedding_model
        model_name = get_embedding_model()
        try:
            ActivityMonitor().increment()
            client = get_ollama_client()
            try:
                resp = await asyncio.wait_for(client.embeddings(model=model_name, prompt=task), timeout=20.0)
            finally:
                ActivityMonitor().decrement()
            task_vec = np.array(resp.embedding[:256])
            keywords = await self._load_keyword_embeddings()
            best_score = 0.5
            best_kw = None
            for kw, kw_vec in keywords.items():
                base_score = TASK_COMPLEXITY_KEYWORDS[kw]
                sim = float(np.dot(task_vec, kw_vec) / (np.linalg.norm(task_vec) * np.linalg.norm(kw_vec) + 1e-8))
                if sim > 0.65 and base_score * sim > best_score:
                    best_score = round(base_score * sim, 2)
                    best_kw = kw
            if best_kw:
                logger.debug(f"SprintContract: Embedding fallback matched '{best_kw}' (score={best_score})")
            return best_score
        except Exception as e:
            logger.warning(f"SprintContract: Embedding complexity failed ({e}), using default")
            return 0.7

    async def _analyze_complexity(self, task: str) -> Dict[str, Any]:
        task_lower = task.lower()
        keyword_scores = []
        for keyword, base_score in TASK_COMPLEXITY_KEYWORDS.items():
            if keyword in task_lower:
                keyword_scores.append(base_score)

        if not keyword_scores:
            complexity = await self._embedding_complexity(task)
        else:
            complexity = sum(keyword_scores) / len(keyword_scores)
            complexity = round(complexity, 2)

        threshold = max(0.5, complexity)
        if "critical" in task_lower or "security" in task_lower or "production" in task_lower:
            threshold = max(threshold, 0.9)

        test_count = 1 if complexity < 0.6 else (2 if complexity < 0.8 else 3)
        required_tests = ["unit"]
        if complexity >= 0.7:
            required_tests.append("lint")
        if complexity >= 0.85:
            required_tests.append("integration")

        return {
            "complexity": complexity,
            "threshold": threshold,
            "required_tests": required_tests,
            "test_count": test_count,
        }

    async def negotiate(self, task: str) -> Dict[str, Any]:
        """
        Negotiates the contract criteria for the given task.
        Uses keyword-based task analysis for realistic complexity scoring.
        """
        logger.info(f"SprintContract: Negotiating criteria for session {self.session_id}")

        complexity_data = await self._analyze_complexity(task)

        contract = {
            "version": "1.0",
            "task_id": self.session_id,
            "task": task[:200],
            "threshold": complexity_data["threshold"],
            "complexity": complexity_data["complexity"],
            "required_tests": complexity_data["required_tests"],
            "success_criteria": [
                "Code follows modular patterns",
                "No hardcoded paths or credentials",
                f"At least {complexity_data['test_count']} test check(s) pass",
                "Error handling covers all exceptions",
                "Output matches contract specification",
            ]
        }

        self.log.append("contract.negotiated", contract)
        logger.info(f"SprintContract: Negotiated threshold={contract['threshold']} complexity={contract['complexity']}")

        return contract

if __name__ == "__main__":
    import asyncio
    async def test():
        sc = SprintContract("test_contract_session")
        contract = await sc.negotiate("Add a new API endpoint")
        print(f"Negotiated Contract: {contract}")
    
    asyncio.run(test())
