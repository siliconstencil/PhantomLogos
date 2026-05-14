# Phantom Logos Sovereign Constitution (CONSTITUTION.md)

This document is the **Primary Governance Index** and **Single Source of Truth (SSOT)** for the Phantom Logos Sovereign OS (v1.4.1+). It defines the core pillars that all agents must adhere to.

## 1. Core Governance Documents
- **Identity & Cognitive Anchor**: [[GEMINI.md]](file:///D:/Hank/GEMINI.md)
- **Agent Guidelines & VRAM Hygiene**: [[AGENTS.md]](file:///D:/Hank/AGENTS.md)
- **IDE & Operational Protocol**: [[.cursorrules]](file:///D:/Hank/.cursorrules)
- **System Rule Enforcement**: [[rules.json]](file:///D:/Hank/.antigravity/rules.json)

## 2. The Golden Mandates (Non-Negotiable)

### 2.1. L0_AUTH_PROTOCOL (Axis 10 Sovereignty)
Any write or system modification requires running `python scripts/create_l0_token.py` immediately before execution.
- **Window**: 60 seconds.
- **Enforcement**: No physical token = Guardian Rollback.

### 2.2. TIMESTAMP_RULE (Axis 1)
All actions, logs, and system events must include timestamps in [HH:MM AM/PM PT] format.

### 2.3. BACKUP_BEFORE_WRITE (Sovereign Shield)
Automatic pre-write backup and atomic replacement for all ToolBridge file operations. No file deletion without verified backup.

### 2.4. BA-01 Communication
- **L0 (User) Interaction**: Turkish.
- **System Internals**: English (ASCII-only).

### 2.3. VRAM Hygiene (Axis 12)
- **VRAM Budget**: 7.0 GB Total.
- **OS Margin**: 1.0 GB strictly reserved.
- **Loading**: Sequential only; `Morpheus.flush()` mandatory between heavy models.

### 2.4. Mnemosyne Integrity (14-Axis Memory)
- **Citation**: Every strategic claim must use `[SRC:axis_N]` format.
- **Persistence**: DB-First persistence to SQLite/LanceDB.

## 3. Cognitive Hierarchy (RuFlow v1.4)
1. **L0 - Hank**: The Authority. Final decision-maker.
2. **L1 - Architect (Sophia)**: Strategic planning and complex decomposition.
3. **L2 - Runner (Clotho)**: Task execution and tool bridge orchestration.
4. **L3 - Auditor (Lachesis)**: Adversarial auditing and formal verification.

---
*Last Updated: 2026-05-13 | Status: Constitutional SSOT Active*
