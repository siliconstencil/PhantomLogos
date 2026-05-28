---
name: 14-axis-memory
description: Mnemosyne 14-axis memory architecture access protocols and autonomous
  querying strategy.
version: 1.0.0
license: MIT
compatibility: opencode
model_role: light
allowed_tools:
- semantic
- mcp_slm_recall
- mcp_slm_search
- mcp_slm_context
- mcp_slm_fetch
tier: 1
---
# Skill: 14-Axis Memory (Mnemosyne)

Defines the strategic access layer for the Mnemosyne 14-axis memory architecture, ensuring high-fidelity context retrieval across all cognitive dimensions.

## Workflow
1.  **Assembly**: Identify which cognitive axes are relevant to the current goal (e.g., Axis 1 for history, Axis 5 for spatial graph).
2.  **Query**: Execute a multi-axis search using semantic and FTS (Full-Text Search) fallbacks.
3.  **Synthesize**: Merge results using the RRF (Reciprocal Rank Fusion) algorithm to prioritize high-confidence matches.
4.  **Inject**: Format the retrieved context into the reasoning window using structured axis-citations (e.g., `[SRC:axis_N]`).
5.  **Reflect**: Store the success or failure of the retrieval in Axis 7 for future optimization.

## Guardrails
- **Confidentiality**: Never retrieve or expose raw PII stored in restricted memory blocks.
- **VRAM Hygiene**: Large memory assembly operations must be profiled before injection to prevent context window overflow.
- **Groundedness**: Every retrieved claim must have an associated `event_key` and timestamp for provenance.

## Output Format
- `retrieved_axes`: List of axes queried during the operation.
- `context_summary`: High-density summary of the synthesized memory.
- `citation_map`: Mapping of claims to their original sources in the DB.
- `fidelity_score`: Confidence score (0.0 - 1.0) of the retrieved context.
