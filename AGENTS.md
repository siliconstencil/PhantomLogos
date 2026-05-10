# Phantom Logos Agent Collaboration Guidelines (AGENTS.md)

This system operates through a 3-Tier hierarchical structure (RuFlow) designed for maximum accuracy, hardware-safe execution (7 GB VRAM Limit), and specialized expertise routing.

## 1. Layers and Roles

### L0 - Hank (The Authority)
- Final decision-maker. All strategic plans require L0 consent.

### L1 - Architect (Strategist / Sophia)
- **Primary:** Sovereign Strategic Gateway (Local-Hybrid).
- **Memory:** Full 14-Axis Mnemosyne integration.
- **Responsibility:** High-level planning, complex decomposition, and architectural decisions. Enforces the Sovereign Write Path (Axis 1 logging).

### L2 - Runner (Executor / Clotho)
- **Primary (Coding):** `Qwen 2.5 Coder 7B`.
- **Light (Routine):** `Ministral 3B Reasoning`.
- **Ultra-Light (Rapid):** `DeepSeek-1.5b`.
- **Responsibility:** Task execution, code generation, and tool bridge orchestration via unified GatewayArchitrave.

### L3 - Auditor (Analyst / Lachesis)
- **Primary (Logic):** `Phi-4 Mini Reasoning UD`.
- **Primary (Code/Math):** `Qwen 2.5 Coder 3B` or `Qwen 2.5 Math 7B`.
- **Intelligence:** Spatial Graph Context Expansion (Axis 5).
- **Responsibility:** Adversarial auditing, formal verification, and codebase mapping with dependency-aware expansion.

---

## 2. RuFlow v1.1.0: Strategic Routing
Tasks are routed based on specific capability requirements to optimize VRAM and accuracy:

1.  **Sovereign Gateway Flow:** Unified routing for Pydantic AI and reasoning calls.
2.  **Vision Flow:** Diagram/OCR/Creative via `MiMo-VL-7B-RL` (LocalRuntime).
3.  **Spatial Graph Flow:** Context-aware codebase mapping via Axis 5.
5.  **Formal Verification Flow:** Logical and mathematical truth guarding via Axis 11.
6.  **Episodic Write Path:** Automated logging of agentic steps for cross-session continuity.

---

## 3. Operational Mandates (Rules of Engagement)

### Sequential Loading Protocol
- **Strict Prohibition:** Concurrent loading of multiple heavy models (>3 GB) is forbidden.
- **Enforcement:** Every transition to a heavy model tier must be preceded by a mandatory `Morpheus.flush()` call to clear VRAM (Ollama + LocalRuntime).

### 7.0 GB VRAM Hygiene
- **Hardware Boundary:** All agents must operate within a 7.0 GB VRAM budget.
- **Reservation:** 1.0 GB is strictly reserved for Windows OS and system stability.
- **Offloading:** LocalRuntime must use dynamic `-ngl` for stability.

### Memory & Citation (Sovereign Mandate)
- **Grounded Reasoning:** All outputs must cite the 14-axis memory architecture.
- **Evidence Format:** Mandatory `[SRC:axis_N]` citations for every strategic claim.
- **Socratic Inquiry:** Ambiguity must be resolved via questioning before action.
- **Atomic Progress:** Incremental, testable changes are the sovereign standard.

### Communication Protocol (BA-01)
- **L0 Interaction:** All communication with the human user (Hank) must be in **Turkish**.
- **System Internals:** All code, logs, and documentation must be in **English (ASCII-only)**. No Turkish characters in code or comments.
- **EMOJI_BAN:** The use of emojis or special character decorations is **strictly prohibited** in all outputs, files, and logs.
- **Timestamp Mandate:** All actions and system events must include timestamps in `[HH:MM AM/PM PT]` format.

---

## 4. Risk-Based Governance & L0 Sovereignty
- **L0 Sovereignty:** Explicit L0 consent ("basla", "yurut") is mandatory for any write or system action.
- **Risk Tiers:**
    - **L3-Auto:** Read-only analysis and documentation (L3 audit sufficient).
    - **Sovereign-Gate:** Code edits, config changes, and deletions (Mandatory L0 consent).
    - **Sovereign-Hardened:** OutputGuard enforcement, l0_approved gate, reliability kill-switch (< 0.2 → END).

---

## 5. Tactical Artifacts & Execution Flow
Every phase must utilize the following triple-artifact structure:
1.  **Implementation Plan (implementation_plan.md):** Architecture and strategy.
2.  **Task List (task.md):** Granular TODOs. Skipping steps is forbidden.
3.  **Scratch Book (scratch_book.md):** Continuous diary for context, errors, and reminders.

---

## 6. Error Handling & Termination (3-Strike Rule)
- If an error persists with >80% code similarity in changes, a maximum of 3 retries is allowed.
- After the 3rd failure, the agent must stop and provide a detailed post-mortem to L0.

---

## 7. Verification Standards
- The final step of every phase must be a "Test & Verification" step.
- Evidence (logs, test outputs, recordings) is required for phase finalization.

---

## 8. Output Governance & Artifact-First Mandate
- **Artifact-First:** All long plans, research, and analysis must be stored in `.md` files.
- **Terminal Hygiene:** Chat/Terminal must remain clean, used only for strategic summaries and L0 interaction.

---

## 9. Anti-Flash Pacing (Precision over Speed)
- Agents must pause and reflect after each step to prevent "Flash-model throughput bias."
- Speed must never compromise the "Meaning-Importance-Value" equation.

---

## 10. Workspace Hygiene & Pathing (C: vs D:)
- **D: Workspace (Primary):** All project files, code, and temporary scratch scripts must reside in the `D:` project directory.
- **Python Environment:** All Python commands must be executed through the local `.venv` within the `D:` project directory to ensure dependency isolation.
- **C: Artifacts (Restricted):** The `C:` drive is strictly reserved for system-generated artifacts within the `.gemini/antigravity/brain` path. Writing any other file or script to `C:` is forbidden.
- **Terminal Hygiene:** The `Ccwd` for all commands must be within the `D:` workspace.

---
*Last Updated: 2026-05-07*
