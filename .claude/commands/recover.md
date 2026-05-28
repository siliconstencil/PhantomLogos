# Error Self-Recovery

Diagnose a tool failure and execute the Sovereign 3-Strike recovery protocol.

## Steps

1. **Diagnose** — Categorize the error:
   - `Transient`: Network timeout, rate limit, temporary resource lock → retryable
   - `Environmental`: Wrong path, missing config, permission denied, schema mismatch → fix context
   - `Logical`: Hallucination, syntax error, invalid parameter, logic loop → change approach

2. **Check Strike Count** — Query Axis 7 (OperationalStore) for the current strike counter on this goal.

3. **Execute Recovery Cascade**:
   - **Strike 1 (Soft Retry)**: Retry with normalized parameters, cleared cache, or corrected file path anchor. Log to Axis 7.
   - **Strike 2 (Hard Fallback)**: Switch to a different tool set or lighter model tier (Tier 0). Log to Axis 7. Report to L0 at next turn.
   - **Strike 3 (Escalation)**: HALT immediately. Generate post-mortem. Request L0-Hank intervention. Do not retry.

4. **Verify Recovery** — Confirm Plan B output resolves the original failure without secondary state corruption.

5. **Rollback Trigger** — If error persists after Strike 2, invoke Sovereign Shield to restore last verified snapshot.

## Output
- `error_type`: Transient / Environmental / Logical
- `strike_status`: 1, 2, or 3
- `recovery_path`: What alternative was tried
- `state_restored`: true/false (rollback triggered)
- `status`: RECOVERED / ESCALATED / FAILED

## Guardrails
- Never retry the exact same command+parameters after a failure.
- All Strike 2 and Strike 3 events must be surfaced to L0 in the next message.
- Fallback operations must stay within 7.0 GB VRAM budget.

Error description: $ARGUMENTS
