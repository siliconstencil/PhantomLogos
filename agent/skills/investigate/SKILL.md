---
name: investigate
description: Systematic root-cause debugging. 5-phase protocol for bugs, regressions, stack traces, and unexpected behavior. No fixes without confirmed root cause.
version: 1.0.0
license: MIT
compatibility: opencode
model_role: primary
allowed_tools:
  - report
  - semantic
  - mapper
  - mcp_slm_recall
  - mcp_slm_remember
  - mcp_slm_observe
tier: 2
when_to_use:
  - User reports a bug, error, or unexpected behavior.
  - Stack trace or error log is present.
  - A regression is suspected ("it was working yesterday").
  - Root cause analysis is requested explicitly.
  - error-self-recovery escalates a Logical-category error to this skill.
metadata:
  audience: developers
  tier: L2-Clotho
  workflow: debug
  axis_primary: 10
  axis_secondary: 11
---
# Skill: Investigate (Sovereign Debug Protocol)

Systematic root-cause debugging adapted from gstack investigate methodology.
Integrated with Phantom Logos Mnemosyne (Axis 10 Rational, Axis 11 Verification).

## Iron Law

**NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST. [SRC:axis_10]**

Fixing symptoms creates whack-a-mole debugging. Every fix that skips root cause
makes the next bug harder to find. Confirm the cause, then fix it.

---

## Pre-flight: Prior Investigation Query

Before starting, query Mnemosyne for prior investigations on the same files or error pattern:

```
mcp_slm_recall: query="investigate root cause <symptom keywords>", limit=5, axis=10
```

If prior investigations exist, note the pattern. Recurring bugs in the same area
signal an architectural smell — flag it before diving in.

---

## Phase 1: Root Cause Investigation

Gather evidence before forming any hypothesis. [SRC:axis_10]

1. **Collect symptoms:** Read error messages, stack traces, reproduction steps.
   Ask ONE clarifying question at a time if context is insufficient.

2. **Read the code:** Trace the code path from symptom to potential cause.
   Use Grep for all references, Read for logic.

3. **Check recent changes:**
   ```
   git log --oneline -20 -- <affected-files>
   ```
   Regression = root cause is in the diff.

4. **Reproduce:** Trigger the bug deterministically before proceeding.
   If intermittent, gather more evidence first.

**Output:** State a specific, testable root cause hypothesis before moving to Phase 2.

---

## Phase 2: Pattern Analysis

Match the symptom against known patterns: [SRC:axis_11]

| Pattern | Signature | Where to look |
|---------|-----------|---------------|
| Race condition | Intermittent, timing-dependent | Concurrent access to shared state |
| Nil/null propagation | TypeError, AttributeError | Missing guards on optional values |
| State corruption | Inconsistent data, partial updates | Transactions, callbacks, hooks |
| Integration failure | Timeout, unexpected response | External API calls, service boundaries |
| Configuration drift | Works locally, fails in prod | Env vars, feature flags, DB state |
| Stale cache | Shows old data, fixes on clear | Redis, CDN, LanceDB, SQLite WAL |
| VRAM overflow | OOM, model load failure | Heavy model transitions without flush |
| Axis desync | Memory retrieval returns stale data | Mnemosyne axis_id mismatch |

Also check: `git log` for prior fixes in the same files. Recurring bugs in the same
files are an architectural smell.

---

## Phase 3: Hypothesis Testing

Before writing ANY fix, verify the hypothesis. [SRC:axis_11]

1. **Confirm:** Add a temporary log statement or assertion at the suspected root cause.
   Run reproduction. Does evidence match?

2. **If wrong:** Gather more evidence. Return to Phase 1. Do not guess.

3. **3-Strike Rule (aligned with error-self-recovery):**
   If 3 hypotheses fail, STOP. Report to L0 with:
   - What was tried (all 3 hypotheses)
   - Evidence gathered
   - Proposed escalation path (architectural review vs. additional logging)

**Red flags — slow down if any appear:**
- Proposing a fix before tracing data flow
- Each fix reveals a new problem elsewhere (wrong layer, not wrong code)
- Strike count 3 without root cause confirmation

**Scope Lock:** After confirming hypothesis, restrict edits to the affected module:
```
Set-Content -Path "D:\Hank\.claude\freeze-dir.txt" -Value "<affected-dir>" -NoNewline
```
Prevents scope creep during fix. Remove with `/unfreeze` after verification.

---

## Phase 4: Implementation

Root cause confirmed — implement the fix. [SRC:axis_1]

1. **Fix the root cause, not the symptom.** Smallest change that eliminates the problem.

2. **Minimal diff:** Fewest files touched, fewest lines changed.
   Do not refactor adjacent code during a bug fix.

3. **Write a regression test:**
   - Must FAIL without the fix
   - Must PASS with the fix

4. **Run full test suite:**
   ```
   PYTHONPATH=. pytest tests/ -v
   ```
   No regressions allowed. Paste output as evidence.

5. **Blast radius check:** If fix touches >5 files, pause and report to L0.
   This typically indicates wrong layer, not wrong code.

6. **VRAM hygiene:** If fix involves model transitions, call `morpheus_flush.py`
   before loading a new heavy model. [SRC:axis_7]

---

## Phase 5: Verification & Report

Fresh verification is mandatory. Reproduce original scenario, confirm fix. [SRC:axis_11]

Output a structured debug report:

```
DEBUG REPORT [SRC:axis_10][SRC:axis_11]
============================================================
Symptom:         [what the user observed]
Root cause:      [what was actually wrong — specific, not generic]
Fix:             [what was changed, file:line references]
Evidence:        [test output, reproduction showing fix works]
Regression test: [file:line of new test]
Related:         [architectural notes, recurring pattern flag if applicable]
Strike count:    [1, 2, or 3 — if 3, escalated to L0]
Status:          DONE | DONE_WITH_CONCERNS | BLOCKED | ESCALATED
============================================================
```

**Log to Mnemosyne (Axis 10):**
```
mcp_slm_remember: content="Investigate: <root_cause_summary> in <file>", axis=10, tags=["investigate", "root_cause", "<affected_module>"]
```

---

## Completion Status

- **DONE** — root cause confirmed, fix applied, regression test written, tests pass
- **DONE_WITH_CONCERNS** — fixed but intermittent bug cannot be fully verified
- **BLOCKED** — root cause unclear after 3 hypotheses, escalated to L0
- **ESCALATED** — architectural issue, requires L0 + full team review

---

## Integration with error-self-recovery

When `error-self-recovery` categorizes an error as `Logical` (hallucination/syntax/logic),
it delegates to this skill. The `strike_status` from error-self-recovery maps to
Phase 3's 3-Strike Rule. A Strike 3 from either skill → immediate L0 escalation.
