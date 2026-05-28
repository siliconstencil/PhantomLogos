---
name: state-bus
description: Agent message bus for inter-agent communication and state sharing across
  the hierarchy.
version: 1.0.0
license: MIT
compatibility: opencode
model_role: expert
allowed_tools:
- report
- mcp_slm_mesh_send
- mcp_slm_mesh_state
- mcp_slm_remember
tier: 3
---
# State Bus

Manages inter-agent message passing and shared state across the 3-tier RuFlow hierarchy.

## Architecture

### Message Bus Pattern
- Agents publish events to named channels (e.g., `draft.ready`, `audit.complete`).
- Subscribers receive events via async callbacks.
- All messages are logged to EpisodicStore (Axis 1) for traceability.

### State Sharing
- Shared state lives in `data/mnemosyne.db` (not in-memory) for crash resilience.
- LangGraph `State` object flows through nodes via `orchestrator.py`.
- Context anchors are injected via `ankyra/anchor_generator.py`.

## Best Practices
- Always use the bus instead of direct method calls between agents.
- Persist critical state before publishing events.
- Subscribe with timeout guards to prevent deadlocks.
