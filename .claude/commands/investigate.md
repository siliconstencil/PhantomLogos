# Investigate (Sovereign Debug Protocol)

Systematic root-cause debugging. No fixes without a confirmed root cause.

## Iron Law

NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST.

## Phase 1: Evidence Collection

1. Read error messages, stack traces, and reproduction steps from $ARGUMENTS.
2. Trace the code path using Grep and Read — do not guess.
3. Check recent changes: `git log --oneline -20 -- <affected-files>`
4. Reproduce the bug deterministically before forming a hypothesis.

**Output:** State a specific, testable root cause hypothesis.

## Phase 2: Pattern Matching

Match symptom against known patterns:

| Pattern | Signature |
|---------|-----------|
| Race condition | Intermittent, timing-dependent |
| Nil/null propagation | TypeError, AttributeError |
| State corruption | Inconsistent data, partial updates |
| Integration failure | Timeout, unexpected response |
| Configuration drift | Works locally, fails in prod |
| Stale cache | Shows old data, clears on restart |
| VRAM overflow | OOM, model load failure |

## Phase 3: Hypothesis Testing

1. Confirm with a targeted log or assertion at the suspected root cause.
2. Run reproduction. Does evidence match?
3. If wrong, return to Phase 1. Do not guess.

**3-Strike Rule:** After 3 failed hypotheses, STOP and deliver a post-mortem.

## Phase 4: Fix

Root cause confirmed. Smallest change that eliminates the problem:
- Fix the root cause, not the symptom.
- Write a regression test that FAILS without the fix and PASSES with it.
- Run: `PYTHONPATH=. pytest tests/ -v` — no regressions allowed.
- Blast radius: if fix touches >5 files, pause and report.

## Phase 5: Verification Report

```
DEBUG REPORT
Symptom:         [observed]
Root cause:      [specific — not generic]
Fix:             [file:line references]
Evidence:        [test output]
Regression test: [file:line]
Strike count:    [1/2/3]
Status:          DONE | DONE_WITH_CONCERNS | BLOCKED
```

Bug, error, or regression to investigate: $ARGUMENTS
