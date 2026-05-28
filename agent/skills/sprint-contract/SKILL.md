---
name: sprint-contract
description: Definition of Done negotiation and sprint scope management between L0
  and agents.
version: 1.0.0
license: MIT
compatibility: opencode
model_role: expert
allowed_tools:
- report
- ls
- verify
- mcp_slm_remember
tier: 3
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

## Engineering Review Gate

Run this gate BEFORE starting implementation of any phase. L0 consent is still required to proceed after the gate passes.

### Step 0: Scope Challenge (MANDATORY — hard stop)

Answer all before proceeding:
1. What existing code already partially solves each sub-problem? Capture outputs from existing flows before building parallel ones.
2. What is the minimum set of changes that achieves the stated goal? Flag any work deferrable without blocking the core objective.
3. Complexity check: if the plan touches >8 non-trivial files (excluding `agent/skills/*/SKILL.md` updates) or introduces >2 new classes/services, STOP. Call AskUserQuestion: name what is overbuilt, propose a minimal version, ask L0 whether to reduce or proceed as-is. Do not edit the plan file or begin implementation until L0 responds.
4. Boring by default: every new infrastructure component or non-standard pattern costs an "innovation token." Flag when a built-in or proven approach exists. Prefer extending existing systems over introducing new ones.
5. Completeness check: AI makes edge-case coverage cheap. Recommend the complete version (full test coverage, all error paths) unless it requires multi-week rewrites.

If the complexity check does not trigger, present Step 0 findings and proceed to the review sections.

### Review Sections (sequential — no skipping)

#### 1. Architecture Review
- Component boundaries and coupling.
- Dependency graph: new dependencies justified?
- Data flow and potential bottlenecks.
- Security: auth boundaries, L0 token scoping, API surface.
- Single points of failure.
- One realistic production failure scenario per new codepath.
- VRAM budget: no two heavy models (>3 GB) loaded concurrently. [SRC:axis_7]

#### 2. Code Quality Review
- DRY violations (flag aggressively).
- Error handling: missing edge cases called out explicitly.
- Over/under-engineered relative to the task size.
- ASCII diagrams in touched files — still accurate after this change?

#### 3. Test Review
- Trace every codepath in the plan (draw ASCII execution diagram for non-trivial flows).
- Map user flows and error states.
- Every conditional branch needs a test.
- Tests must FAIL without the fix, PASS with it.
- Run `PYTHONPATH=. pytest tests/ -v` — no regressions allowed.

#### 4. Performance Review
- N+1 query patterns.
- VRAM budget compliance: check model load sequence for flush opportunities. [SRC:axis_7]
- Concurrency hazards (shared state, async lock ordering).
- LanceDB / SQLite WAL patterns for bulk writes.

### Pre-emit Verification Gate

Before reporting any finding:
1. Quote the specific file:line that motivates it.
2. If the motivating line cannot be quoted, the finding is unverified — suppress from main report, include in appendix only.
3. Confidence below 7/10 — appendix only.

Finding format:
```
[SEVERITY] (confidence: N/10) file:line — description
```

Severity levels: P0 (data loss / security), P1 (functional breakage), P2 (correctness risk), P3 (quality / maintainability).
