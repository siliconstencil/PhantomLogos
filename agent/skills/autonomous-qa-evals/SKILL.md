---
name: autonomous-qa-evals
description: Alias — redirects to the comprehensive audit skill. See agent/skills/audit/SKILL.md for the full 6-phase audit pipeline.
version: 2.0.0
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
  - Full system audit, static analysis, security scan, or pre-release quality gate.
metadata:
  audience: developers
  tier: L3-Auditor
  workflow: quality-assurance
  redirect: agent/skills/audit/SKILL.md
---

# Autonomous QA & Evals

**MERGED INTO `audit` skill.**

This skill has been consolidated into the comprehensive [audit](SKILL.md) pipeline.
The `audit` skill provides a 6-phase system-scanning pipeline:

1. Static Analysis (ruff + pyright)
2. Dependency Audit
3. Logic Audit (L3 Lachesis: SymPy + Z3 + QWED + LLM)
4. Security Audit (OWASP, secrets, injection)
5. E2E Audit (pytest, mapper)
6. Report (structured scores, verdict)

**Load the `audit` skill instead of this one.**
