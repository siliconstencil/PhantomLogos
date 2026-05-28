import os
from typing import Any

import numpy as np
import tiktoken

from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)

# Matryoshka & Atropos Configuration
DEFAULT_TOKEN_ENCODING = os.getenv("TOKEN_ENCODING", "cl100k_base")

DEFAULT_TIER_LIMITS = {
    "reasoning": int(os.getenv("TOKEN_TIER_REASONING", "3000")),
    "task": int(os.getenv("TOKEN_TIER_TASK", "4000")),
    "global": int(os.getenv("TOKEN_TIER_GLOBAL", "5000")),
}


class ContextPruner:
    """
    Atropos Context Engineering: multi-tier token-aware pruning.
    Applies importance-based ranking and strict token budgeting.
    """

    def __init__(self, model_encoding: str = DEFAULT_TOKEN_ENCODING) -> None:
        self.encoder = tiktoken.get_encoding(model_encoding)
        self.tier_limits = dict(DEFAULT_TIER_LIMITS)
        self.budget_exceeded = False

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
            logger.warning("ContextPruner: Matryoshka initialization failed (%s)", e)

        self.arbitrator: Any = None
        try:
            from cognition.mnemosyne.memory_arbitrator import MemoryArbitrator

            self.arbitrator = MemoryArbitrator()
        except ImportError:
            pass

        self.meta_store: Any = None
        try:
            from cognition.mnemosyne.meta_cognition import MetaCognitionStore

            self.meta_store = MetaCognitionStore()
        except ImportError:
            pass

        self.budget_guard: Any = None
        try:
            from .token_budget import get_token_guard

            self.budget_guard = get_token_guard()
        except ImportError:
            pass

    def count_tokens(self, text: str) -> int:
        """
        Precise token counting via tiktoken (Sovereign mode).
        Cloud API calls removed as per Phase 11.6 guidelines.
        """
        return len(self.encoder.encode(text))

    async def prune_context(
        self,
        memories: list[dict[str, Any]],
        token_limit: int = 4000,
        agent_id: str = "system",
        query_text: str | None = None,
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
                logger.warning("ContextPruner: Semantic embedding failed (%s)", ee)

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
            semantic_score = 0.5  # Default if no query
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

    async def prune_by_tier(
        self, memories: list[dict[str, Any]], tier: str, query_text: str | None = None
    ) -> list[dict[str, Any]]:
        limit = self.tier_limits.get(tier, 4000)
        return await self.prune_context(memories, token_limit=limit, query_text=query_text)

    def slice_context_window(self, full_context: str, tier: str) -> str:
        """
        Tier-based context slicing for LLM injection with Axis prioritization.
        Guarded against None, empty, or malformed contexts with early exit and try/except backup.
        """
        if not full_context or not isinstance(full_context, str) or not full_context.strip():
            return ""

        try:
            limit = self.tier_limits.get(tier, 4000)

            # Split into blocks by markdown headings
            import re

            raw_parts = re.split(r"(?m)^### ", full_context)

            blocks = []
            # First part might be text before the first ###
            if raw_parts and raw_parts[0].strip():
                blocks.append({"header": "", "content": raw_parts[0], "axis": 0, "index": 0})
                start_idx = 1
            else:
                start_idx = 0

            for i, part in enumerate(raw_parts[1:]):
                lines = part.split("\n", 1)
                header = lines[0]
                content = lines[1] if len(lines) > 1 else ""

                # Find axis number
                axis_match = re.search(r"\bAXIS\s+(\d+)\b", header, re.IGNORECASE)
                axis_id = int(axis_match.group(1)) if axis_match else 0

                blocks.append(
                    {
                        "header": f"### {header}",
                        "content": content,
                        "axis": axis_id,
                        "index": start_idx + i,
                    }
                )

            # Count tokens for each block
            for b in blocks:
                b["text"] = b["header"] + ("\n" if b["header"] else "") + b["content"]
                b["tokens"] = self.count_tokens(b["text"])

            # Sort blocks by priority (lower is higher priority)
            AXIS_PRIORITY = {  # noqa: N806
                0: 0,  # Special blocks/Anchor
                8: 1,
                11: 2,
                10: 3,
                3: 4,
                1: 5,
                7: 6,
                13: 7,
                2: 8,
                5: 9,
                6: 10,
                9: 11,
                4: 12,
                14: 13,
                12: 14,
                15: 15,
            }

            sorted_blocks = sorted(blocks, key=lambda x: AXIS_PRIORITY.get(x["axis"], 99))

            selected_indices = set()
            current_tokens = 0

            for b in sorted_blocks:
                if current_tokens + b["tokens"] <= limit:
                    selected_indices.add(b["index"])
                    current_tokens += b["tokens"]

            # Fallback to standard slicing if we couldn't select any blocks
            if not selected_indices:
                token_ids = self.encoder.encode(full_context)
                if len(token_ids) <= limit:
                    pruned_text = full_context
                    final_tokens = len(token_ids)
                else:
                    half = limit // 2
                    start_ids = token_ids[:half]
                    end_ids = token_ids[-half:]
                    truncated_ids = start_ids + end_ids
                    pruned_text = self.encoder.decode(truncated_ids)
                    final_tokens = len(truncated_ids)
            else:
                # Reconstruct text keeping original order
                selected_blocks = [b for b in blocks if b["index"] in selected_indices]
                pruned_text = "\n".join(b["text"] for b in selected_blocks)
                final_tokens = current_tokens

            # Set budget exceeded flag and consume tokens
            self.budget_exceeded = False
            if self.budget_guard:
                try:
                    success = self.budget_guard.consume(final_tokens)
                    if not success:
                        self.budget_exceeded = True
                except Exception as e:
                    logger.warning(
                        "ContextPruner: Failed to consume tokens in budget guard (%s)", e
                    )

            return pruned_text
        except Exception as e:
            logger.error(f"ContextPruner: Failed during slice_context_window ({e})")
            # Fail-safe backup fallback: try crude slicing or return empty string to prevent total pipeline crash
            try:
                limit = self.tier_limits.get(tier, 4000)
                token_ids = self.encoder.encode(full_context)
                if len(token_ids) <= limit:
                    return full_context
                return self.encoder.decode(token_ids[:limit])
            except Exception:
                return ""


if __name__ == "__main__":
    test_pruner = ContextPruner()

    sample_memories = [
        {
            "text": "Very important fact about the project architecture",
            "importance": 1.0,
            "timestamp": 100,
        },
        {"text": "Less important historical note", "importance": 0.5, "timestamp": 101},
        {"text": "Old critical security rule", "importance": 0.9, "timestamp": 50},
        {"text": "Minor style preference", "importance": 0.2, "timestamp": 102},
    ]
    for t_name in ("reasoning", "task", "global"):
        pruned_res = test_pruner.prune_by_tier(sample_memories, t_name)
        print(f"Tier [{t_name}] limit={test_pruner.tier_limits[t_name]}: {len(pruned_res)} items")

    LONG_TEXT = "The quick brown fox " * 300
    sliced_res = test_pruner.slice_context_window(LONG_TEXT, "reasoning")
    print(
        f"Slice test: {len(LONG_TEXT)} -> {len(sliced_res)} chars, tokens={test_pruner.count_tokens(sliced_res)}"
    )
