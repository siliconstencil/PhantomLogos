# Mnemosyne High-Fidelity Query

Query the 14-axis Mnemosyne memory system for context relevant to the given topic or goal.

## Steps

1. **Identify Target Axes** — Determine which cognitive dimensions are relevant:
   - Axis 1 (Episodic): Past decisions and agent steps
   - Axis 2 (Procedural): Tool call history and patterns
   - Axis 3 (Goals): Active objectives and their status
   - Axis 4 (Temporal): Time-ordered event sequences
   - Axis 5 (Spatial/Graph): Codebase structure and dependencies
   - Axis 6 (Semantic): Conceptual knowledge
   - Axis 7 (Operational): Runtime metrics and tool outcomes
   - Axis 8 (Meta-Cog): Self-monitoring patterns
   - Axis 10 (Rational): Facts and governance assertions
   - Axis 11 (Verification): Formal proof outcomes
   - Axis 13 (Cross-Session): Patterns across sessions

2. **Hybrid Search** — Execute both:
   - Vector path: semantic similarity via LanceDB (Axis 6 weight: 0.7)
   - FTS path: keyword/BM25 search (weight: 0.3)

3. **RRF Merge** — Combine results using Reciprocal Rank Fusion.

4. **Temporal Filter** — Discard results superseded by more recent events (Axis 4).

5. **Output** with mandatory `[SRC:axis_N]` citations:
   - `top_matches`: Relevant memory fragments with citations
   - `axes_covered`: Which axes were queried
   - `fidelity_score`: Confidence 0.0 – 1.0
   - `temporal_range`: Earliest and latest event timestamps

## Guardrails
- Every claim must include `[SRC:axis_N]` citation.
- Discard fragments with relevance score < 0.35.
- If `data/mnemosyne.db` is unavailable, report clearly and do not hallucinate.

Query topic: $ARGUMENTS
