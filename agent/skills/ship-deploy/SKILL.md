---
name: ship-deploy
description: Release automation pipeline - build verification, test execution, artifact preparation, and deployment coordination.
version: 1.0.0
license: MIT
compatibility: opencode
model_role: primary
allowed_tools:
  - run_code
  - verify
  - report
  - ls
  - mcp_slm_remember
  - mcp_slm_recall
  - semantic
tier: 2
when_to_use:
  - User requests a release or deployment.
  - Build and test automation before merge.
  - Artifact generation and version bumping.
  - Deployment coordination across environments.
metadata:
  audience: developers
  tier: L2-Runner
  workflow: release
---

# Skill: Ship / Deploy

Release automation pipeline covering the full lifecycle: build -> test -> stage -> deploy. Designed for both local (development/CI) and future cloud targets.

## Workflow

1.  **Preflight (setup-deploy):** Verify environment readiness. Check Git status, dependency integrity, and VRAM/model availability. Run `verify` on all changed modules.

2.  **Build (ship):** Run the build command (e.g., `pip install -e .`, `pytest tests/`). Capture build artifacts and log to Axis 1 (Episodic Store). If build fails, produce a failure report and stop.

3.  **Test Gate (land):** Execute the full test suite. Enforce threshold: >= 90% pass rate, zero critical failures. Log test results to Axis 4 (Temporal Store) for trend analysis.

4.  **Stage (canary):** If a staging environment is available, deploy incrementally (canary subset). If not, produce a dry-run deployment manifest with rollback instructions.

5.  **Deploy (land-and-deploy):** Execute deployment. Tag the release in Git. Update CHANGELOG.md. Log to Axis 13 (Cross-Session) for Hermes bridge visibility.

## Guardrails
- NEVER ship with failing tests (0 critical, >= 90% overall).
- ALWAYS generate a rollback plan before any deploy step.
- Version bump must follow semver (MAJOR.MINOR.PATCH).
- Respect Sovereign Shield: snapshot pre-deployment state before any destructive action.
- For cloud deployments, require L0 auth token (basla / yurut).

## Output Format
- `release_manifest`: Version, hash, artifact paths, environment targets.
- `test_summary`: Pass/fail/skip counts, coverage delta.
- `deploy_log`: Timestamped steps with exit codes.
- `rollback_plan`: Step-by-step undo procedure.
