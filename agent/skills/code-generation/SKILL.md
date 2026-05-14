---
name: code-generation
description: High-performance code generation following clean architecture and SOTA patterns.
version: 1.1.0
license: MIT
compatibility: opencode
when_to_use:
  - User requests a new feature implementation.
  - Refactoring existing code for better performance or modularity.
  - Generating unit tests or integration scripts.
metadata:
  audience: developers
  tier: L2-Runner
  workflow: execution
---

# Skill: Code Generation

High-performance code generation following clean architecture and SOTA patterns.

## Workflow
1.  **Analyze**: Study the existing codebase (Axis 5) to ensure architectural consistency.
2.  **Design**: Outline the module structure, classes, and function signatures.
3.  **Implement**: Write deterministic, ASCII-only code with standard error handling.
4.  **Verify**: Perform static analysis and run unit tests before completion.

## Guardrails
- NO Turkish characters in code or comments (BA-01 Compliance).
- NO emojis or special decorations (EMOJI_BAN).
- ALWAYS use absolute paths for file operations.
- Ensure all dependencies are imported and correctly scoped.

## Output Format
- Fenced code blocks with language identifiers.
- Brief explanation of design decisions.
- Unit test examples for the generated code.
