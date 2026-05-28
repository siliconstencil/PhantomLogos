---
name: hermes-bridge
description: Cross-system verification and DB-first persistence auditing protocol.
version: 1.1.0
license: MIT
compatibility: opencode
model_role: light
allowed_tools:
- verify
- report
- mcp_slm_remember
- ls
tier: 1
---
# Hermes Bridge Audit Protocol

## 1. Claim Verification
Every "done" or "success" claim must be validated against Mnemosyne DB records.
- For tool calls: Check `OperationalStore` or `ProceduralStore`.
- For state changes: Check `EpisodicStore` (Axis 1).
- For fact assertions: Check `RationalStore` (Axis 10).

## 2. Session Lifecycle
Strict adherence to the CLI lifecycle is mandatory:
1. `init`: Start session.
2. `load`: Pull context.
3. `verify`: Audit findings.
4. `save`: Record results.
5. `close`: Seal session.

## 3. DB-First Rule
Absolutely no operational findings shall be written to `.md`, `.json`, or `.log` files.
Persistence must flow exclusively to `data/mnemosyne.db`.

## 4. Socratic Inquiry
Ask at least 3 investigative questions before approving complex architectural changes.
- Why is this change necessary?
- What are the VRAM/Token implications?
- How does it affect the 14-axis alignment?
