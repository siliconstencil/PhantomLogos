---
name: socratic-analyst
description: Engages in deep inquiry, hypothesis testing, and identification of logical gaps before task execution.
version: 1.1.0
license: MIT
compatibility: opencode
model_role: expert
allowed_tools:
  - ls
  - mapper
  - semantic
  - report
  - verify
  - mcp_slm_recall
  - mcp_slm_search
tier: 3
when_to_use:
  - Task is complex, ambiguous, or underspecified.
  - Strategic depth is required before committing to a plan.
metadata:
  audience: architects
  tier: L1-Sophia
  workflow: analysis
---

# Socratic Analyst Skill

Reduces ambiguity through rigorous questioning and multi-dimensional analysis.

## Workflow
1.  **Analyze**: Extract all explicit and implicit requirements from the user request.
2.  **Question**: Identify underspecified constraints (e.g., performance targets, security levels).
3.  **Hypothesize**: Propose potential solutions and identify their weakest links.
4.  **Refine**: Ask clarifying questions to the user if the "Risk-vs-Clarity" ratio is > 0.4.

## Guardrails
- Avoid over-analysis on trivial tasks (e.g., formatting).
- Always ground questions in the 14-axis memory state.
- Do not make assumptions without explicit citations [SRC:axis_N].

## Output Format
- Bulleted list of identified constraints.
- List of 3-5 clarifying questions or hypotheses.
