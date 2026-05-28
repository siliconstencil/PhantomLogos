---
name: mnemosyne-write-path
description: Enforcing DB-first persistence via Mnemosyne Axis 1 Episodic Store write
  path logging.
version: 1.0.0
license: MIT
compatibility: opencode
model_role: light
allowed_tools:
- mcp_slm_remember
- mcp_slm_observe
- mcp_slm_report_outcome
tier: 1
---
# Mnemosyne Write Path

Every agent action must be recorded to the Mnemosyne database, not to flat files.

## Core Rule

**No operational finding shall be written to `.md`, `.json`, or `.log` files.**
All persistence flows exclusively to `data/mnemosyne.db`.

## Write Targets

| Store | Axis | When |
|-------|------|------|
| EpisodicStore | Axis 1 | Every agent step / decision |
| ProceduralStore | Axis 2 | Every tool call and its result |
| GoalStore | Axis 3 | Objective state changes |
| RationalStore | Axis 10 | Facts and governance assertions |

## Best Practices
- Call `episodic_store.log()` at the start and end of every agent step.
- Use `procedural_store.record_usage()` after every tool execution.
- Never skip the write path - it is the source of truth for cross-session continuity.
- Reference [SRC:axis_1] for step history.
