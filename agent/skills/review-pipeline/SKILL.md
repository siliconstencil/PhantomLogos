---
name: review-pipeline
description: Multi-AI code review pipeline with architectural audit, code review, and cross-model second opinion.
version: 1.0.0
license: MIT
compatibility: opencode
model_role: expert
allowed_tools:
  - mapper
  - verify
  - report
  - semantic
  - mcp_slm_remember
  - mcp_slm_recall
  - ls
  - run_code
tier: 3
when_to_use:
  - Architecture changes or major refactors requiring structural audit.
  - Security-critical code paths needing adversarial review.
  - Any pull request or merge candidate before integration.
  - Suspicious logic or potential regression detection.
metadata:
  audience: developers
  tier: L3-Auditor
  workflow: review
---

# Skill: Review Pipeline

Multi-AI code review pipeline with three phases: architectural audit, detailed code review, and cross-model second opinion. Leverages L3 Lachesis as the primary auditor with optional multi-model consensus verification.

## Workflow

1.  **Plan Review (plan-eng-review):** Study the codebase topography (Axis 5) and the proposed change. Evaluate architectural fit, dependency impact, and layer violations. Use mapper to trace affected modules.

2.  **Code Review (review):** Run Lachesis three-pass audit (AST -> QWED -> Z3/LLM) on the diff. Check for logic errors, anti-patterns, BA-01 violations, and security vulnerabilities. Produce structured CritiqueResult with confidence score.

3.  **Second Opinion (codex):** If confidence < 0.8, route the diff to a secondary model (Qwen 3.5 4B or DeepSeek-R1-8B) for independent review. Cross-validate findings. Log divergence as Axis 11 verification records.

4.  **Merge Gate:** Only approve when both primary and secondary reviews pass (confidence >= 0.7). Generate a review summary with signatures.

## Guardrails
- NEVER approve a merge if architectural integrity score < 0.8.
- ALWAYS run full pipeline for security-critical paths (db/, auth/, gateway/).
- Respect Sovereign Shield snapshots: trigger a pre-write backup before any recommended change.
- L3 Lachesis audit is mandatory; codex second opinion is optional based on confidence threshold.

## Output Format
- `review_summary`: Phase-by-phase results with confidence scores.
- `violations`: List of detected issues with severity (critical/major/minor).
- `recommendation`: approve / conditional / reject with rationale.
- `cross_model_divergence`: Only present if codex was invoked.
