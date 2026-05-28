---
name: error-self-recovery
description: Autonomous tool failure recovery and fallback execution protocols.
version: 1.0.0
license: MIT
compatibility: opencode
model_role: light
allowed_tools:
  - report
  - semantic
  - mcp_slm_remember
  - mcp_slm_observe
tier: 1
when_to_use:
  - Tool execution returns an error (e.g., Permission Denied, File Not Found).
  - Environment mismatch detected during runtime.
metadata:
  audience: developers
  tier: L2-Clotho
  workflow: recovery
---
# Skill: Error Self-Recovery (Sovereign Edition)

Enables agents to diagnose tool failures and attempt alternative paths (Plan B) without halting the session. Implements the Sovereign 3-Strike Rule with Axis 7 Operational Audit integration.

## Workflow
1.  **Diagnose**: Categorize the error as `Transient` (retryable), `Environmental` (path/config mismatch), or `Logical` (hallucination/syntax/logic error).
    - **For `Logical` errors:** Delegate immediately to the `investigate` skill (5-phase root-cause protocol). Do not attempt a fix before root cause is confirmed. [SRC:axis_10]
2.  **Audit Strike Count**: Query the `OperationalStore` (Axis 7) to retrieve the strike counter for the current goal.
3.  **Execute Fallback Cascade**:
    - **Strike 1 (Soft Retry)**: Retry with normalized parameters, cleared cache, or directory anchoring fix.
    - **Strike 2 (Hard Fallback)**: Switch to a different tool set or a lighter model (Tier 0) to bypass logic loops.
    - **Strike 3 (Escalation)**: Immediate halt. Generate a post-mortem report and request L0-Hank intervention.
4.  **Verification**: Confirm that the Plan B output resolves the original failure without secondary state corruption.
5.  **Rollback**: If the error state persists, invoke `Sovereign Shield` to restore the last verified file system snapshot.

## Guardrails
- **Recursive Protection**: Never attempt the exact same command/parameter combination more than once after a failure.
- **7GB VRAM Hygiene**: Fallback operations must remain within hardware limits; favor Tier 0 models if headroom < 1.0 GB.
- **L0 Sovereignty**: All "Strike 2" and "Strike 3" events must be reported to L0 in the next communication turn.

## Output Format
- `error_type`: Categorization (Transient, Environmental, Logical).
- `strike_status`: Current strike count (1, 2, or 3).
- `recovery_path`: Detailed description of the alternative strategy executed.
- `state_restored`: Boolean indicating if a Sovereign Shield rollback was required.
- `status`: Outcome (RECOVERED, ESCALATED, or FAILED).
