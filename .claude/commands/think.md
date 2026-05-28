# Sequential Thinking

Break down a complex problem into ordered, revisable reasoning steps using the Sequential Thinking MCP server.

## When to Use

- Multi-causal debugging where the cause chain is not obvious.
- Architectural decisions with competing trade-offs.
- Any task where backtracking or revising earlier steps is likely.

## Steps

1. **Initialize** — Call `sequentialthinking` with:
   - `thought`: First reasoning step
   - `thoughtNumber`: 1
   - `totalThoughts`: Estimated steps (update as you go)
   - `nextThoughtNeeded`: true

2. **Iterate** — Continue step by step, each building on the previous.

3. **Branch** (when needed) — Set `branchFromThought` + `branchId` to explore an alternative path without discarding the main chain.

4. **Revise** (when needed) — Set `needsRevising: true` and re-call with a corrected thought.

5. **Complete** — Set `nextThoughtNeeded: false` on the final step.

## Example Trace

```
Thought 1: The timeout occurs after 30s — matches SLM warmup window.
Thought 2: Checking mcp_config.json — env is empty, SLM_DISABLE_WARMUP_SIDE_EFFECTS not set.
  Branch 2a: Could Ollama being down cause the hang?
Thought 3 (revising 2): Doctor confirms Ollama HTTP 404. Warmup tries Ollama, hangs 30s.
Thought 4: Fix: add SLM_DISABLE_WARMUP_SIDE_EFFECTS=1 to mcp_config.json env.
```

## Guardrails
- Commit to at least 3 thoughts before forming a conclusion.
- Use branching when you catch yourself guessing — explore both paths.
- Do not skip to conclusions; the value is in the visible trace.

Problem to reason through: $ARGUMENTS
