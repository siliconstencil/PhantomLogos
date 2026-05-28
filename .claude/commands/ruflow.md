# RuFlow Tier Routing

Analyze the given task and determine the optimal execution tier following the RuFlow v1.1.0 architecture.

## Steps

1. **Complexity Analysis** — Evaluate the task against:
   - Axis 11 (Math/Logic): Does it require formal verification or proofs?
   - Axis 5 (Spatial): Does it require codebase graph traversal or dependency mapping?
   - Axis 6 (Semantic): Does it require deep conceptual reasoning?

2. **Tier Assignment**:
   - **Tier 0 (Ultra-Light)**: Routine tasks, syntax checks, formatting → `deepscaler-1.5b`
   - **Tier 1 (Light)**: Fast reasoning, template generation, memory queries → `ministral-3b`
   - **Tier 2 (Primary)**: Standard coding, tool orchestration → `qwen3.5-4b` / Clotho
   - **Tier 3 (Expert/Cloud)**: Complex architecture, formal verification, complexity > 0.8 → **Claude Code CLI** (orchestrates Sophia+Clotho roles via sub-agent spawn) or Gemini CLI (native parallel multi-agent)

   **CLI routing note:**
   - `Claude Code CLI` → Tier 3, single orchestrator + sub-agent spawn, handles L1+L2 roles internally
   - `Gemini CLI` → Tier 3, native parallel multi-agent, full RuFlow coverage
   - `OpenCode/DeepSeek` → Tier 1-2, single orchestrator, sequential execution
   - All CLI agents bridge through **Hermes** for cross-session memory sync

3. **VRAM Check** — Confirm the selected tier fits within the 7.0 GB budget (1.0 GB OS reserve).

4. **Output**:
   - `assigned_tier`: 0, 1, 2, or 3
   - `reasoning_model`: Selected model name
   - `complexity_score`: 0.0 – 1.0
   - `escalation_triggered`: true/false
   - `rationale`: One sentence justification

## Guardrails
- Never route to a heavy model (>3 GB) if current VRAM > 6.0 GB without scheduling a `morpheus_flush` first.
- Strategic plan changes (implementation_plan.md edits) MUST be routed to Tier 1 minimum.
- Formal verification tasks always use temperature=0 at Tier 3.

Analyze the task: $ARGUMENTS
