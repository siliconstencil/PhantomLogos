# Socratic Analyst

Engage deep inquiry mode to reduce ambiguity before committing to a plan. Use when a task is complex, underspecified, or carries architectural risk.

## Steps

1. **Extract Requirements** — From the input, identify:
   - Explicit requirements (stated directly)
   - Implicit requirements (assumed but unstated)
   - Conflicting constraints

2. **Hypothesis Generation** — Propose 2-3 potential solution paths. For each:
   - State the core assumption
   - Identify the weakest link
   - Estimate complexity score (0.0 – 1.0)

3. **Gap Analysis** — Identify what is unknown or underspecified:
   - Performance targets
   - Security level requirements
   - VRAM / hardware constraints
   - Cross-session continuity needs

4. **Clarifying Questions** — If Risk-vs-Clarity ratio > 0.4, generate 3-5 targeted questions:
   - Ground each question in a specific axis `[SRC:axis_N]`
   - Order by impact (highest uncertainty first)
   - Do NOT ask about trivial formatting or naming decisions

5. **Output**:
   - Bulleted list of identified constraints (explicit + implicit)
   - 3-5 clarifying questions OR a go/no-go recommendation if clarity is sufficient
   - Recommended RuFlow tier for execution

## Guardrails
- Do not apply to trivial tasks (formatting, variable renaming, single-file edits).
- Never make assumptions without citing `[SRC:axis_N]`.
- Sycophancy is prohibited — prioritize system integrity over agreement.

Task to analyze: $ARGUMENTS
