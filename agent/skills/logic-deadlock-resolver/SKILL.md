---
name: logic-deadlock-resolver
description: Resolving adversarial loops and hallucination spirals via constraint
  relaxation.
version: 1.0.0
license: MIT
compatibility: opencode
model_role: primary
allowed_tools:
- verify
- report
- semantic
- mcp_slm_remember
tier: 2
---
# Skill: Logic Deadlock Resolver (Sovereign Edition)

Autonomously identifies reasoning spirals and adjusts contract thresholds or decomposes tasks to break through complex logical deadlocks.

## Workflow
1.  **Spiral Detection**: Monitor Axis 7 for repetitive reasoning patterns or "hallucination spirals" where the model repeats failing logic.
2.  **Constraint Identification**: Extract the core constraints preventing progress (e.g., conflicting rules, tool limitations, or hardware boundaries).
3.  **Relaxation Strategy**:
    - **Tier Shift**: Move the task from a lower-reasoning model (Tier 2/3) to a higher-reasoning model (Tier 1 - Sophia) for deep analysis.
    - **Constraint Relaxation**: Temporarily lower non-critical thresholds (e.g., code coverage from 90% to 80%) to achieve a working baseline.
    - **Atomic Decomposition**: Break the deadlocked task into smaller, independent sub-goals.
4.  **Verification**: Ensure the relaxed approach still meets the absolute minimum safety and integrity standards defined in `ankyra_anchor.md`.
5.  **Re-anchoring**: Once the deadlock is broken, gradually restore original constraints for final hardening.

## Guardrails
- **Non-Negotiables**: Core Sovereign OS governance rules and L0 security mandates are NEVER subject to relaxation.
- **Socratic Pause**: If relaxation fails twice, initiate a Socratic inquiry turn to ask L0 for environmental clarification.
- **VRAM Stability**: Tier shifts must be validated against the 7GB hygiene limit before execution.

## Output Format
- `deadlock_cause`: Analysis of why the original path failed.
- `relaxed_constraints`: List of thresholds that were adjusted.
- `decomposition_plan`: Granular breakdown of the new sub-tasks.
- `re_anchoring_path`: Plan to restore full integrity after the breakthrough.
