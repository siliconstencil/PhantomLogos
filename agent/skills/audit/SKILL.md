---
name: audit
description: Comprehensive 6-phase system audit pipeline (static analysis, dependency audit, logic audit, security audit, e2e audit, report). Scans entire codebase with ruff, pyright, pytest, mapper, and L3 verifiers.
version: 1.0.0
license: MIT
compatibility: opencode
model_role: expert
allowed_tools:
  - mapper
  - verify
  - report
  - semantic
  - run_code
  - mcp_slm_remember
  - mcp_slm_recall
  - ls
tier: 3
when_to_use:
  - Full system audit before release or after major changes.
  - Identifying code quality issues, security vulnerabilities, and logic errors.
  - Ensuring zero-bug delivery and architectural integrity.
  - Post-implementation verification and quality gate.
  - Pre-deployment sanity check.
metadata:
  audience: developers
  tier: L3-Auditor
  workflow: quality-assurance
---

# Skill: Audit Pipeline

Comprehensive 6-phase system audit that scans the entire codebase with professional-grade tools. Merges autonomous QA evals with multi-AI review pipeline into a single authoritative audit process.

## 6-Phase Pipeline

### Phase 1: Static Analysis
Run ruff linter + formatter and pyright type checker across the entire `src/` tree. Use --no-fix to see all violations without auto-correction.

**Checklist:**
- `ruff check src/ --no-fix` — catalog all lint violations by severity
- `ruff format src/ --check` — detect formatting drift
- `pyright` (or `pyright src/`) — catalog type errors (0-error policy)

**Output:** Total violation count, top-5 most violated rules, any type errors.

### Phase 2: Dependency Audit
Scan dependencies for license compliance, known vulnerabilities, and unused packages.

**Checklist:**
- Check `pyproject.toml` and `.venv/Lib/site-packages/` for outdated or vulnerable packages
- Run `pip-audit` if available, or manually inspect critical dependencies
- Verify `tool.ruff.lint` in pyproject.toml is complete and matches actual codebase usage
- Check for unused imports across the codebase with `ruff check --select F401`

### Phase 3: Logic Audit
Run L3 Lachesis formal verification pipeline against code changes.

**Checklist:**
- AST parse check on modified files
- QWED 2-pass logic verification (2B primary -> 4B expert if score < 0.6)
- SymPy symbolic evaluation for mathematical expressions
- Z3 SAT solver for constraint satisfaction
- LLM reasoning audit via Phi-4 Mini
- Cross-reference with Axis 11 (reflection_store) for historical verification records

### Phase 4: Security Audit
Scan for OWASP Top 10 patterns, hardcoded secrets, path traversal, injection risks.

**Checklist:**
- `ruff check --select S` — bandit-style security rules
- Grep for hardcoded API keys, tokens, passwords (`api_key`, `secret`, `password`, `token = `)
- Check subprocess usage for shell injection (`shell=True`, unsanitized input)
- Verify Sovereign Shield is active (file_watchdog, snapshot_manager)
- Check L0_AUTH_TOKEN compliance on write operations

### Phase 5: E2E Audit
Run the full test suite and mapper verification.

**Checklist:**
- `pytest tests/ -v --tb=short` — all tests pass (target: 100%)
- `python scripts/discover_id.py` — mapper layer violation check (target: 0)
- Check spatial.db for stale modules or orphaned dependencies
- Verify 14-axis memory stores are healthy (queries return within expected latency)

### Phase 6: Report
Generate a structured audit report with phase-by-phase scores.

**Output:**
- `audit_summary`: Phase-by-phase results with pass/fail/score
- `violations`: Full list of detected issues with severity (critical/major/minor/warning)
- `recommendation`: pass / conditional / fail with rationale
- `structural_integrity_score`: 0.0-1.0 based on mapper health
- `quality_gate_verdict`: Overall verdict with blocking vs non-blocking items

## Guardrails
- NEVER skip pyright check — 0-error policy is mandatory
- ALWAYS run E2E tests before marking audit as passed
- Respect Sovereign Shield: trigger pre-write backup if audit recommends changes
- If Phase 3 (Logic Audit) finds UNSAT or confidence < 0.6, escalate to deadlock_resolver
- Do not auto-fix violations in Phase 1 — catalog first, fix later

## When to Skip Phases
- Quick pre-commit check: Phase 1 + Phase 4 only (static + security)
- Logic-only change: Phase 3 only
- Release gate: All 6 phases mandatory
