# System Audit Pipeline

Comprehensive 6-phase audit before release, major refactor, or after significant changes.

## Phase 1: Static Analysis

```bash
ruff check src/ --no-fix
ruff format src/ --check
mypy src/
```

Output: violation count, top-5 violated rules, type errors (0-error policy).

## Phase 2: Dependency Audit

- Check `pyproject.toml` for outdated or vulnerable packages.
- Run `pip-audit` if available.
- Check for unused imports: `ruff check --select F401`

## Phase 3: Logic Audit

- AST parse check on modified files.
- Review control flow for off-by-one errors, missing guards, and edge cases.
- Cross-reference recent `git log` for prior fixes in same files (recurring = architectural smell).

## Phase 4: Security Audit

```bash
ruff check --select S
```

- Grep for hardcoded secrets: `api_key`, `secret`, `password`, `token =`
- Check subprocess calls for `shell=True` with unsanitized input.
- Verify L0_AUTH_TOKEN compliance on all write operations.

## Phase 5: E2E Audit

```bash
PYTHONPATH=. pytest tests/ -v --tb=short
python scripts/health_check_14_axes.py
```

- All tests pass (target: 100%).
- 14-axis memory stores healthy.

## Phase 6: Report

```
AUDIT REPORT
Phase 1 Static:    PASS/FAIL — [violation count]
Phase 2 Deps:      PASS/FAIL — [findings]
Phase 3 Logic:     PASS/FAIL — [findings]
Phase 4 Security:  PASS/FAIL — [findings]
Phase 5 E2E:       PASS/FAIL — [test results]
Quality Gate:      PASS | CONDITIONAL | FAIL
Blocking items:    [list]
```

## Quick Modes

- Pre-commit: Phase 1 + Phase 4 only.
- Logic-only change: Phase 3 only.
- Release gate: All 6 phases mandatory.

## Guardrails
- Never auto-fix in Phase 1 — catalog first, fix later with explicit L0 consent.
- If Phase 3 finds 3+ recurring bugs in same file, flag as architectural smell.

Scope (module, file, or "full"): $ARGUMENTS
