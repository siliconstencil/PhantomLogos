---
name: context-slicing
description: Intelligent context pruning and sliding window management for long sessions.
version: 1.1.0
license: MIT
compatibility: opencode
model_role: light
allowed_tools:
- report
- mcp_slm_remember
- ls
tier: 1
---
# Skill: Context Slicing

Optimizes information density by removing redundant or low-value context fragments.

## Workflow
1.  **Analyze**: Identify tokens belonging to old turns, repetitive thoughts, or large irrelevant logs.
2.  **Filter**: Apply importance-weighting to keep critical artifacts (Plan, Task, Scratch).
3.  **Slice**: Use the `prune` tool to enforce 4k, 8k, or 20k window boundaries.
4.  **Inject**: Provide a condensed summary of the pruned data to maintain continuity.

## Guardrails
- NEVER prune the active Implementation Plan or Task List.
- Maintain at least the last 2 turns of full conversation logs.
- Use Axis 12 (Efficiency) to track pruning-to-performance ratios.

## Output Format
- Pre-pruning token count.
- Post-pruning token count.
- List of preserved critical artifacts.
