# Antigravity Skills Library (Q2 2026 Sovereign)

This directory contains specialized expertise and persona-based skills used within the system's "Phantom Logos" hierarchical architecture. All skills follow the **SOTA 2026 Agent Skills Specification** for deterministic execution.

## Personas & Specialists
- [persona-runner](./persona-runner/SKILL.md): **L2 Executor** - Operational implementation and rapid coding.
- [persona-auditor](./persona-auditor/SKILL.md): **L3 Auditor** - Process analysis and quality control.
- [socratic-analyst](./socratic-analyst/SKILL.md): **L1 Architect** - Strategic inquiry and logic verification.
- [security-first-guardian](./security-first-guardian/SKILL.md): **L3 Security** - Data privacy and supply chain integrity.

## Core Operational Skills (Clotho)
- [code-generation](./code-generation/SKILL.md): Production-ready implementation patterns.
- [file-operations](./file-operations/SKILL.md): Atomic and secure filesystem management.
- [vision-analysis](./vision-analysis/SKILL.md): Multimodal UI and diagram analysis.
- [agent-orchestrator](./agent-orchestrator/SKILL.md): Architectural decomposition and delegation.
- [mnemosyne-write-path](./mnemosyne-write-path/SKILL.md): DB-first persistence via Mnemosyne write path.
- [local-runtime](./local-runtime/SKILL.md): llama.cpp subprocess and dynamic -ngl management.
- [state-bus](./state-bus/SKILL.md): Inter-agent message passing and state sharing.

## System Lifecycle Skills (Morpheus)
- [model-lifecycle](./model-lifecycle/SKILL.md): VRAM optimization and model state management.
- [vram-monitoring](./vram-monitoring/SKILL.md): Real-time hardware boundary enforcement.
- [telemetry](./telemetry/SKILL.md): Operational metrics and latency reporting.
- [resource-scheduling](./resource-scheduling/SKILL.md): Computational load balancing and token budgeting.
- [background-agent](./background-agent/SKILL.md): Persistent daemon and scheduled task management.

## Optimization & Memory (Atropos)
- [context-slicing](./context-slicing/SKILL.md): Sliding window context pruning.
- [token-budget](./token-budget/SKILL.md): Sustainable computational cost control.
- [prompt-compression](./prompt-compression/SKILL.md): High-density semantic token distillation.
- [temporal-validity](./temporal-validity/SKILL.md): Time-respecting retrieval with event_key supersede lifecycle.

## Governance & Protection
- [sovereign-shield](./sovereign-shield/SKILL.md): File integrity, snapshot management, and atomic rollback.
- [sprint-contract](./sprint-contract/SKILL.md): DoD negotiation and sprint scope management.

## Quality & Audit
- [autonomous-qa-evals](./autonomous-qa-evals/SKILL.md): Zero-bug delivery and test-driven validation.
- [hermes-bridge](./hermes-bridge/SKILL.md): 14-Axis Mnemosyne verification and DB-first auditing.
- [security-audit](./security-audit/SKILL.md): OWASP vulnerability scanning and dependency CVE checks.
- [ui-design-premium](./ui-design-premium/SKILL.md): Premium aesthetic interface engine.

## Connectivity & Integration
- [sovereign-gateway](./sovereign-gateway/SKILL.md): Local proxy management and Pydantic AI hijack protocols.
- [mcp-orchestration](./mcp-orchestration/SKILL.md): JIT MCP tool discovery and dynamic binding.

## Skill Standards (SOTA 2026)
Every skill is a self-contained expert module:
1. **Discovery (Frontmatter):** Uses `when_to_use` for trigger optimization and `metadata` for routing.
2. **Permission Gating:** Enforced via `allowed-tools` and `opencode.json` governance.
3. **Internal Documentation:** Procedural Markdown checklists for machine activation.
