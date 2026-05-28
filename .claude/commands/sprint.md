# Sprint Contract

Formalize a sprint phase agreement between L0 (Hank) and the agent hierarchy. Produces the three mandatory artifacts.

## Prerequisites
- Explicit L0 consent obtained: "basla" or "yurut"
- Valid `L0_AUTH_TOKEN` confirmed (run `python scripts/create_l0_token.py` if needed)

## Artifacts to Produce

### 1. `implementation_plan.md`
- Phase title and version
- Objective in one sentence
- Architecture decisions with rationale
- Success criteria (measurable)
- Risks and mitigation

### 2. `task.md`
- Granular TODOs numbered sequentially
- Each task: description + acceptance criterion
- Status: [ ] pending / [x] done
- No step-skipping allowed

### 3. `scratch_book.md`
- Running diary initialized with session timestamp `[HH:MM AM/PM PT]`
- Sections: Context, Errors, Decisions, Reminders

## Definition of Done Checklist
- [ ] All task.md items completed and verified
- [ ] `pytest tests/ -v` passes
- [ ] L3 audit (`python scripts/sovereign_audit.py`) passed without critical findings
- [ ] Evidence (test output, logs) attached
- [ ] L0 approval obtained for phase finalization

## Output
Produce all three artifact files for the requested sprint phase. Ask clarifying questions first if scope is ambiguous (Risk-vs-Clarity ratio > 0.4).

Sprint description: $ARGUMENTS
