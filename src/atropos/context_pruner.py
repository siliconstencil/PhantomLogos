import os
from collections.abc import Sequence
from typing import Any

import numpy as np
import tiktoken

from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)

# Matryoshka & Atropos Configuration
DEFAULT_TOKEN_ENCODING = os.getenv("TOKEN_ENCODING", "cl100k_base")

DEFAULT_TIER_LIMITS = {
    "reasoning": int(os.getenv("TOKEN_TIER_REASONING", "4000")),
    "task": int(os.getenv("TOKEN_TIER_TASK", "8000")),
    "global": int(os.getenv("TOKEN_TIER_GLOBAL", "20000")),
}


class ContextPruner:
    """
    Atropos Context Engineering: multi-tier token-aware pruning.
    Applies importance-based ranking and strict token budgeting.
    """

    def __init__(self, model_encoding: str = DEFAULT_TOKEN_ENCODING):
        self.encoder = tiktoken.get_encoding(model_encoding)
        self.tier_limits = DEFAULT_TIER_LIMITS

        # Axis Priority Map from .env
        self.axis_priority_map = {
            5: float(os.getenv("CONTEXT_PRIORITY_AXIS_5", "0.7")),
            6: float(os.getenv("CONTEXT_PRIORITY_AXIS_6", "0.7")),
            12: float(os.getenv("CONTEXT_PRIORITY_AXIS_12", "0.9")),
        }

        # Phase 1.0.29: Semantic Awareness (Axis 4)
        try:
            from src.utils.service_locator import get_matryoshka
            self.matryoshka = get_matryoshka()
        except Exception as e:
            self.matryoshka = None
            logger.warning(f"ContextPruner: Matryoshka initialization failed ({e})")

        try:
            from cognition.mnemosyne.memory_arbitrator import MemoryArbitrator

            self.arbitrator = MemoryArbitrator()
        except ImportError:
            self.arbitrator = None

        try:
            from cognition.mnemosyne.meta_cognition import MetaCognitionStore

            self.meta_store = MetaCognitionStore()
        except ImportError:
            self.meta_store = None

        try:
            from .token_budget import get_token_guard

            self.budget_guard = get_token_guard()
        except ImportError:
            self.budget_guard = None

    def count_tokens(self, text: str) -> int:
        """
        Precise token counting via tiktoken (Sovereign mode).
        Cloud API calls removed as per Phase 11.6 guidelines.
        """
        return len(self.encoder.encode(text))

    async def prune_context(
        self, memories: list[dict[str, Any]], token_limit: int = 4000, agent_id: str = "system", query_text: str = None
    ) -> list[dict[str, Any]]:
        """
        Prunes memories based on FIR scores and Semantic Similarity (Axis 4).
        Includes meta-cognitive reliability weighting.
        """
        reliability = 1.0
        if self.meta_store:
            reliability = self.meta_store.get_reliability(agent_id)

        # Phase 1.0.30: Semantic Ranking via Matryoshka
        query_vec = None
        if query_text and self.matryoshka:
            try:
                query_vec = await self.matryoshka.embed_query(query_text)
            except Exception as ee:
                logger.warning(f"ContextPruner: Semantic embedding failed ({ee})")

        scored_items = []
        for mem in memories:
            # 1. Base FIR Score (Axis 6: Memory Arbitrator)
            axis = mem.get("axis", 0)
            importance = mem.get("importance", 0.5)
            is_protected = importance >= self.axis_priority_map.get(axis, 1.1)

            fir_score = 1.0
            if self.arbitrator:
                fir_score = self.arbitrator.score(
                    importance=importance if not is_protected else 1.0,
                    timestamp=mem.get("timestamp", 0),
                    frequency=mem.get("frequency", 1),
                    reliability=reliability,
                )
            
            # 2. Semantic Similarity Score (Axis 4)
            semantic_score = 0.5 # Default if no query
            if query_vec is not None and self.matryoshka and mem.get("text"):
                try:
                    # We use embed_document for memories to match prefix
                    mem_vec = await self.matryoshka.embed_document(mem["text"])
                    semantic_score = float(np.dot(query_vec, mem_vec))
                except Exception:
                    semantic_score = 0.0

            # 3. Combined Ranking (Weighted FIR 40% + Semantic 60%)
            final_score = (fir_score * 0.4) + (semantic_score * 0.6)
            scored_items.append((final_score, mem))

        sorted_memories = [
            item[1] for item in sorted(scored_items, key=lambda x: x[0], reverse=True)
        ]

        pruned = []
        current_tokens = 0
        for mem in sorted_memories:
            mem_tokens = self.count_tokens(mem.get("text") or "")
            if current_tokens + mem_tokens <= token_limit:
                pruned.append(mem)
                current_tokens += mem_tokens

        # Consolidate budget consumption
        if self.budget_guard:
            self.budget_guard.consume(current_tokens)

        return pruned

    async def prune_by_tier(self, memories: list[dict[str, Any]], tier: str, query_text: str = None) -> list[dict[str, Any]]:
        limit = self.tier_limits.get(tier, 4000)
        return await self.prune_context(memories, token_limit=limit, query_text=query_text)

    def slice_context_window(self, full_context: str, tier: str) -> str:
        """
        Tier-based context slicing for LLM injection.
        reasoning: 4000 tokens (Critic/Draft focused)
        task:      8000 tokens (full task awareness)
        global:   20000 tokens (RAG-heavy operations)
        """
        limit = self.tier_limits.get(tier, 4000)
        token_ids = self.encoder.encode(full_context)
        if len(token_ids) <= limit:
            return full_context
        half = limit // 2
        start_ids = token_ids[:half]
        end_ids = token_ids[-half:]
        truncated_ids = start_ids + end_ids
        return self.encoder.decode(truncated_ids)


if __name__ == "__main__":
    pruner = ContextPruner()

    test_memories = [
        {
            "text": "Very important fact about the project architecture",
            "importance": 1.0,
            "timestamp": 100,
        },
        {"text": "Less important historical note", "importance": 0.5, "timestamp": 101},
        {"text": "Old critical security rule", "importance": 0.9, "timestamp": 50},
        {"text": "Minor style preference", "importance": 0.2, "timestamp": 102},
    ]
    for tier in ("reasoning", "task", "global"):
        pruned = pruner.prune_by_tier(test_memories, tier)
        print(f"Tier [{tier}] limit={pruner.tier_limits[tier]}: {len(pruned)} items")

    long_text = "The quick brown fox " * 300
    sliced = pruner.slice_context_window(long_text, "reasoning")
    print(
        f"Slice test: {len(long_text)} -> {len(sliced)} chars, tokens={pruner.count_tokens(sliced)}"
    )
