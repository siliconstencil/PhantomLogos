---
name: autoplan
description: Automated planning and review pipeline - decomposes tasks, assigns agents, runs reviews, and tracks execution.
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
  - mcp_slm_session_init
  - ls
tier: 3
when_to_use:
  - Complex multi-step tasks requiring automated decomposition.
  - Tasks that need architectural review before execution.
  - User requests a full lifecycle flow: plan -> review -> execute.
  - New feature development with multiple modules.
metadata:
  audience: developers
  tier: L1-Architect
  workflow: orchestration
---

# Skill: Autoplan

Automated end-to-end planning and execution pipeline. Decomposes complex requests into atomic tasks, assigns to appropriate agents, runs architectural and code reviews, and tracks progress through completion. Integrates with agent-orchestrator for task dispatch and review-pipeline for quality gates.

## Workflow

1.  **Decompose:** Analyze the request. Break into atomic, dependency-ordered sub-tasks using mapper (Axis 5) for contextual awareness. Generate a structured task graph.

2.  **Assign:** Map each sub-task to the optimal agent tier (L0 for ultra-light, L2 Clotho for execution, L3 Lachesis for audit). Consider VRAM budget and model availability.

3.  **Review Gate (autoplan -> review-pipeline):** Before any execution, run architectural review on the plan. Check for circular dependencies, missing modules, and feasibility.

4.  **Execute:** Dispatch tasks sequentially or in parallel respecting dependency order. Log each step to Axis 1 (Episodic Store).

5.  **Synthesize:** Collect all outputs. Run a final integrity check (mapper integrity score). Generate a plan summary with completion status per sub-task.

## Guardrails
- NEVER skip the architectural review gate (step 3) for plans with > 3 sub-tasks.
- ALWAYS respect VRAM budget (7 GB) when assigning concurrent tasks.
- Enforce dependency order: no task starts until its dependencies are complete.
- If any sub-task fails verification twice, route to deadlock_resolver (aporia).
- Log the full plan to Axis 3 (Goal Store) for session continuity.

## Output Format
- `task_graph`: Dependency-ordered task list with agent assignments.
- `review_gate_result`: Architectural review outcome (approve / revise / reject).
- `execution_log`: Per-task status with timestamps and exit codes.
- `integrity_score`: Final structural integrity score (0.0 - 1.0).
