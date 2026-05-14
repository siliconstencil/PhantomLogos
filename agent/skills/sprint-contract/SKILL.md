---
name: sprint-contract
description: Definition of Done negotiation and sprint scope management between L0 and agents.
version: 1.0.0
license: MIT
compatibility: opencode
when_to_use:
  - Negotiating task scope and acceptance criteria with L0.
  - Defining Definition of Done (DoD) for a sprint.
  - Managing phase transitions and milestone tracking.
  - Creating and updating implementation plans.
metadata:
  audience: developers
  tier: L1-Architect
  workflow: planning
---
# Sprint Contract

Formalizes the agreement between L0 (Hank) and the agent hierarchy for each sprint phase.

## Key Artifacts

### 1. Implementation Plan (`implementation_plan.md`)
- Architecture and strategy document.
- Phase objectives and success criteria.

### 2. Task List (`task.md`)
- Granular TODOs with status tracking.
- No step-skipping allowed.

### 3. Scratch Book (`scratch_book.md`)
- Continuous diary for context, errors, and reminders.

## Definition of Done
- All task items completed and verified.
- L3 audit passed without critical findings.
- Evidence (logs, test outputs) provided.
- L0 approval obtained for phase finalization.

## Best Practices
- Always get explicit L0 consent ("basla", "yurut") before starting a phase.
- Document all scope changes in the scratch book.
- Verify DoD before marking any phase complete.
