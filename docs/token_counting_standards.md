# Token Counting & Work Done Standards for Antigravity OS

This document defines the ground-truth calculation logic for model usage and computational weight within the Antigravity Sovereign Gateway, as of May 2026.

## 1. The "Work Done" Model (Computational Weight)
Antigravity has shifted from linear token counting to a **Work Done** model. Usage is calculated based on the complexity of the agentic task.

- **High Weight Tasks**: Multi-file refactoring, autonomous debugging loops, parallel browser testing.
- **Low Weight Tasks**: Single-file explanation, simple chat, documentation summary.
- **Model Multipliers**:
    - Gemini 3.1 Pro: ~4.5x weight vs Flash.
    - Claude Opus 4.7: ~5.0x weight vs Sonnet.
    - GPT-OSS 120B: High memory weight, medium compute weight.

## 2. Quota & Refresh Governance
The system operates on a dual-layer Fair Usage Policy (FUP):

| Quota Tier | Duration | Refresh Rate | Impact of Exhaustion |
|------------|----------|--------------|----------------------|
| **Sprint** | 5 Hours | Automated | Switch to light/local models |
| **Marathon**| 7 Days | Hidden | **System Lockout (5-7 days)** |

> [!IMPORTANT]
> Hitting the **Marathon Cap** overrides the 5-hour Sprint refresh. This is a hard safety gate implemented by Google to prevent server abuse.

## 3. Local-Hybrid Calculation Logic
To prevent Marathon Lockouts, the Sovereign Gateway MUST perform local pre-auditing of tasks:
1. **Token Count (BPE)**: Manual count using model-specific tokenizers (tiktoken `o200k_base` for GPT-OSS, spm for Gemini).
2. **Complexity Analysis**: Measuring the number of expected tool calls and file system operations.
3. **Efficiency Guard (Axis 12)**: Throttling agents if they enter recursive "oops" loops that inflate "Work Done" without progress.

## 4. Pending Debt (DEBT)
- **[DEBT] MCP-Based Compute Auditor**: Implementation of an MCP server to calculate real-time "Work Done" weight across all network agents (Sophia/Clotho/Lachesis) to ensure 0.98+ stability without hitting weekly limits.

---
*Last Updated: 2026-05-12 | Source: Verified Antigravity Release Notes (May 2026)*
