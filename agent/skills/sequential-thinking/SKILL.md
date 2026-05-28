---
name: sequential-thinking
description: Structured reasoning via Sequential Thinking MCP. Breaks down complex problems into ordered steps with branching, revision, and visual trace.
version: 1.0.0
license: MIT
compatibility: opencode
model_role: expert
allowed_tools:
  - sequential-thinking_sequentialthinking
  - mcp_slm_recall
  - report
tier: 3
when_to_use:
  - Complex multi-step reasoning or analysis tasks.
  - Debugging deep logic chains or multi-causal problems.
  - Architectural decisions with multiple trade-offs.
  - Any task where chain-of-thought reasoning benefits from structured backtracking.
metadata:
  audience: developers
  tier: L1-Strategist
  workflow: reasoning
---

# Skill: Sequential Thinking

Breaks down complex problems into ordered, visible reasoning steps using the Sequential Thinking MCP server. Each step can be revised, branched, or revisited — providing a structured thought trace.

## Tool Interface

`sequential-thinking_sequentialthinking` accepts:
- `thought`: Current reasoning step content
- `nextThoughtNeeded`: Whether more steps are required (boolean)
- `thoughtNumber`: Current step number
- `totalThoughts`: Estimated total steps (update as you go)
- `branchFromThought`: (optional) Branch from a previous step
- `branchId`: (optional) Branch identifier
- `needsRevising`: (optional) Flag to mark a step for revision

## Workflow

1. **Initialize**: Call with `thought`, `nextThoughtNeeded=true`, `thoughtNumber=1`, `totalThoughts=<estimate>`
2. **Iterate**: Continue with sequential steps, updating `thoughtNumber` and `totalThoughts`
3. **Branch** (when needed): Set `branchFromThought` + `branchId` to explore alternatives
4. **Revise** (when needed): Set `needsRevising=true` on a step, then re-call with corrected thought
5. **Complete**: Set `nextThoughtNeeded=false` on final step

## When to Use

- Replace unstructured CoT with visible, revisable thought traces
- Complex debugging: trace cause-effect chains step by step
- Architecture: evaluate trade-offs with branching
- Audit: combine with L3 Lachesis verification for explainable AI reasoning

## Example

```
Thought 1: The bug occurs in payment flow when amount > 1000.
Thought 2: Looking at process_payment(), I see a missing overflow check.
  Branch 2a: Alternative - maybe it's a DB type constraint?
Thought 3 (revising 2): Actually the DB is DECIMAL(10,2), so overflow is at 99,999,999.99. Not the issue.
Thought 4: Confirmed - missing check in validate_amount(). Fix: add upper bound guard.
```
