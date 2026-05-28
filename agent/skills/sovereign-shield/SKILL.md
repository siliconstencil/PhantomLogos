---
name: sovereign-shield
description: File integrity protection, snapshot management, and atomic rollback for
  the Sovereign Shield system.
version: 1.0.0
license: MIT
compatibility: opencode
model_role: primary
allowed_tools:
- verify
- ls
- report
- mcp_slm_remember
tier: 2
---
# Skill: Sovereign Shield (Sovereign Edition)

Enforces file system integrity through a 3-layer protection system (Snapshot, Watchdog, L0-Auth) and provides autonomous management of recovery points.

## Workflow
1.  **Protect**: Register a file or directory for monitoring; trigger an immediate SHA-256 snapshot.
2.  **Monitor**: Background polling of `mtime` and file size; detect deltas against the `Sovereign Registry`.
3.  **Detect**: On unauthorized change detection, freeze the process and verify the `L0_AUTH_TOKEN` (60s TTL).
4.  **Rollback**:
    - **Soft Rollback**: Restore file content from the `.snapshots.db`.
    - **Hard Rollback**: Use `git checkout` for version-controlled files or full directory restoration for system anchors.
5.  **Audit**: Log the violation and restoration path to Axis 11 (Security Audit Store) for post-mortem analysis.

## Guardrails
- **Immutable Logs**: Integrity violation logs are append-only and cannot be modified by L2 agents.
- **Critical Anchors**: Files like `meta_cognition.py` and `ankyra_anchor.md` are under "Root Lock" and require direct L0 manual consent for any modification.
- **Rollback Limit**: If more than 3 rollbacks occur within 5 minutes, the system enters `SAFE_MODE` and halts.

## Output Format
- `snapshot_id`: Unique identifier for the recovery point.
- `integrity_status`: Current health status (SECURE, COMPROMISED, RECOVERING).
- `rollback_details`: Description of the files restored and the method used.
- `auth_token_status`: Validity of the L0 session token.
