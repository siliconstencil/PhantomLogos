# Phase 1.0.3 K0.4: Antigravity Architecture & Quota Research
**Status**: COMPLETED (2026-05-12)

## 1. Factual Architecture (Grounded)
- **Antigravity Server**: A local-hybrid Gateway operating at `localhost:32553`.
- **Communication Protocols**:
    - **A2A (Agent-to-Agent)**: JSON-RPC for inter-agent delegation.
    - **MCP (Model Context Protocol)**: Tool and resource connectivity.
    - **ACP (Agent Client Protocol)**: IDE and session synchronization.

## 2. "Work Done" Token Logic
- Antigravity has deprecated linear token counting in favor of **Computational Weight (Work Done)**.
- **Task Multipliers**: Multi-file edits and autonomous loops increase the "Work Done" score significantly faster than single-turn chat.
- **Model Multipliers**: Gemini 3.1 Pro (~4.5x) and Claude Opus (~5.0x) carry higher weights.

## 3. Quota Governance (Sprint & Marathon)
- **Sprint**: 5-hour refresh cycle for active sessions.
- **Marathon**: 7-day hidden hard cap. Exceeding this triggers a **5-7 day system lockout**.

## 4. Resolution & Borç
- Documentation finalized in `docs/token_counting_standards.md`.
- **[BORÇ]**: Added task to implement a **Compute Auditor MCP Server** for local task-weight pre-verification to prevent weekly Marathon lockouts.

---
*Signed,*
**Antigravity (Phantom Logos)**
