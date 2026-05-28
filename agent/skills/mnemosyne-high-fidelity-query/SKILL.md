---
name: mnemosyne-high-fidelity-query
description: Intelligent 14-axis memory retrieval with semantic reranking.
version: 1.1.0
license: MIT
compatibility: opencode
model_role: light
allowed_tools:
- semantic
- mcp_slm_recall
- mcp_slm_search
- mcp_slm_rerank
tier: 1
---
# Skill: Mnemosyne High-Fidelity Query (Sovereign Edition)

Optimizes context injection by executing a hybrid search cascade across all 14 cognitive axes, merging vector embeddings with full-text search (FTS) for maximum accuracy.

## Workflow
1.  **Hybrid Search**:
    - **Vector Path**: Execute a semantic query using LanceDB + Nomic-Embed-V1.5 (Axis 6).
    - **FTS Path**: Execute a keyword search using BM25/FTS on the target tables.
2.  **RRF Merge**: Combine results from both paths using Reciprocal Rank Fusion (RRF) to normalize disparate scoring systems.
3.  **Jina Rerank**: Dispatch the top 20 RRF results to the `jina-reranker-v3` (via local runtime) for final semantic validation against the goal.
4.  **Temporal Filter**: Filter out results that have been superseded by more recent events (Axis 4).
5.  **Inject**: Present the final top-tier fragments with [SRC:axis_N] citations.

## Guardrails
- **Score Threshold**: Discard any fragment that drops below a Jina relevance score of 0.35.
- **Weights**: Use a 0.7 semantic / 0.3 keyword weight bias unless the task is strictly a "grep-style" search.
- **Fallback**: If LanceDB is unavailable, fall back to FTS-only with a warning to L0.

## Output Format
- `top_matches`: List of fragments with [SRC:axis_N] citations.
- `rrf_scores`: Normalized hybrid scores for the top results.
- `jina_relevance`: Final semantic score from the reranker.
- `axes_covered`: cognitive dimensions included in the final synthesis.
