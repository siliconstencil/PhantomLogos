# Contributing to Phantom Logos

Welcome to the development of the first Sovereign Agentic OS. This document outlines the technical standards for extending the system.

---

## 1. Adding a New Memory Axis (Mnemosyne)

Memory axes are the "long-term storage" of the OS. To add a new axis:

1.  **Define Schema:** Add the table definition to `.antigravity/schema.sql`.
2.  **Create Store:** Create a new class in `cognition/mnemosyne/` (e.g., `temporal_store.py`).
3.  **Inherit Base:** Use the shared SQLite/LanceDB connection logic from `utils/logging_config.py`.
4.  **Register Axis:** Add the AXIS_ID to the `AXIS_MAP` in `topography.md`.
5.  **Integration:** Wire the store into `cognition/sophia/hephaestus.py` via a `_get_X()` singleton and add it to `gnosis/` for context injection.

---

## 2. Adding a New Tool (ToolBridge)

Tools are the "hands" of the OS. To add a tool:

1.  **Implementation:** Add the tool logic as a handler in `src/clotho/bridge/` (e.g., `fs.py` for filesystem tools).
2.  **Registration:** Add the tool name to the `execute()` dispatch map in `ToolBridge`.
3.  **Whitelist:** Add the tool name to the relevant agent's YAML file in `agent/` (e.g., `sophia.yaml`).
4.  **Documentation:** Update `.antigravity/tools.md` with the new capability and its VRAM impact.

---

## 3. Sophia Triple-Loop Reasoning Logic (Wisdom Layer)

Sophia uses a decoupled architecture with three specialized modules:

1.  **Sophia Core (`sophia.py`):** Manages the Draft-Critique-Refine loop.
2.  **Gnosis (`gnosis/`):** Handles 14-axis context assembly.
3.  **Hephaestus (`hephaestus.py`):** Provides singleton tool access and shared schemas.

**Standard:** Never bypass the Critique phase for code-generating tasks.

---

## 4. Coding Standards

- **BA-01:** English comments and variable names. No Turkish in code.
- **Typing:** Use Python type hints (`typing` module) for all function signatures.
- **Locking:** Any singleton accessed by multiple agents must use `threading.Lock`.
- **Logging:** Use `src.utils.logging_config.setup_logger`. Never use `print()`.

---
*Signed,*
**Antigravity (Phantom Logos)**
