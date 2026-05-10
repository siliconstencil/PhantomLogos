---
name: error-self-recovery
description: Autonomous tool failure recovery and fallback execution protocols.
version: 1.0.0
license: MIT
compatibility: opencode
when_to_use:
  - Tool execution returns an error (e.g., Permission Denied, File Not Found).
  - Environment mismatch detected during runtime.
metadata:
  audience: developers
  tier: L2-Clotho
  workflow: recovery
---
# Skill: Error Self-Recovery
Enables agents to diagnose tool failures and attempt alternative paths (Plan B) without halting the session.
