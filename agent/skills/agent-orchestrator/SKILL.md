---
name: agent-orchestrator
description: Autonomously plans complex projects, delegates tasks to specialist agents, and manages multi-stage workflows.
version: 1.2.0
license: MIT
compatibility: opencode
when_to_use:
  - Large-scale requests requiring architectural decomposition.
  - Multi-step execution involving multiple agents.
metadata:
  audience: developers
  tier: L1-Architect
  workflow: orchestration
allowed-tools:
  - ls
  - mapper
  - report
  - verify
---

# Agent Orchestrator Skill (2026 Edition)

Delegates and monitors sub-tasks to ensure high-level goals are met with architectural integrity.

## Workflow
1.  **Decompose**: Break the primary task into atomic, sequential sub-tasks.
2.  **Assign**: Map each sub-task to the most appropriate specialist agent (Clotho for execution, Lachesis for audit).
3.  **Validate**: Before delegating, verify that dependencies between sub-tasks are clearly defined.
4.  **Synthesize**: Collect outputs from all agents and assemble the final solution.

## Guardrails
- NEVER assign a destructive task without a prior backup step.
- Ensure Lachesis audits any critical code before it is passed to the user.
- Maintain a session-wide consistency check (Axis 14) at each stage.

## Output Format
- Clear decomposition list.
- Rationale for each agent assignment.
- Expected outcome per sub-task.
