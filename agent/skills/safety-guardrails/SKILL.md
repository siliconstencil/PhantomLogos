---
name: safety-guardrails
description: Operational safety layer - pre-flight checks, change freeze, continuous guard monitoring, and freeze release for Sovereign infrastructure protection.
version: 1.0.0
license: MIT
compatibility: opencode
model_role: expert
allowed_tools:
  - verify
  - report
  - mapper
  - semantic
  - mcp_slm_remember
  - mcp_slm_recall
  - ls
tier: 3
when_to_use:
  - Before any destructive file operation or config change.
  - Critical infrastructure protection during active development.
  - System integrity verification after incidents.
  - Locking down specific paths or modules from modification.
  - Releasing a freeze after resolution.
metadata:
  audience: developers
  tier: L1-Architect
  workflow: safety
---

# Skill: Safety Guardrails

Four-mode operational safety system inspired by gstack's careful/freeze/guard/unfreeze. Integrates with Sovereign Shield for file integrity monitoring and L0 Auth Protocol for authorization. Each mode provides a specific safety posture.

## Modes

### careful — Pre-Flight Safety Check
Before any write, config change, or deployment:
1. Check Sovereign Shield snapshot integrity (SHA-256 compare).
2. Verify L0 auth token validity (60s window).
3. Run mapper to detect potential circular dependencies or layer violations.
4. Check VRAM headroom if a model load is required.
5. If any check fails, block the operation and report all violations.

### freeze — Change Freeze
Lock specific paths or entire modules against modification:
1. Register guarded paths in Sovereign Shield's snapshot manifest.
2. Set an in-memory freeze flag for the session.
3. Any write_file/replace_content on a frozen path is intercepted and blocked.
4. Log freeze activation to Axis 1 (Episodic Store) with L0 identity.
5. Duration: indefinite until explicit unfreeze.

### guard — Continuous Monitoring
Passive integrity watcher during active development:
1. Poll Sovereign Shield integrity at configurable interval (default: 60s).
2. Detect unauthorized file modifications, permission changes, or new files in guarded paths.
3. On violation: log to Axis 8 (Meta-Cognition), notify L0, and optionally auto-rollback.
4. Guard does NOT block operations — it monitors and reports.

### unfreeze — Release Freeze
Release a previous freeze:
1. Verify L0 auth token (mandatory for unfreeze).
2. Remove guarded paths from the freeze manifest.
3. Clear in-memory freeze flag.
4. Log unfreeze to Axis 1 with L0 identity and duration of freeze.
5. Run a post-unfreeze integrity check to confirm no corruption occurred during freeze.

## Guardrails
- unfreeze REQUIRES L0 auth token (basla / yurut). No exceptions.
- careful is MANDATORY before any operation with tier >= 3 or involving db/ files.
- freeze does NOT persist across sessions — re-apply on session start if needed.
- guard must never trigger on files modified by an authorized (L0-approved) operation.
- ALWAYS log all four modes to Axis 1 with agent_id, timestamp, and outcome.

## Output Format
- `careful_report`: Pre-flight check results with pass/fail per check.
- `freeze_manifest`: List of frozen paths with activation timestamp.
- `guard_alert`: Violation report with file path, change type, and severity.
- `unfreeze_report`: Released paths, freeze duration, integrity check result.
