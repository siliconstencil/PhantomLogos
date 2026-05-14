---
name: state-bus
description: Agent message bus for inter-agent communication and state sharing across the hierarchy.
version: 1.0.0
license: MIT
compatibility: opencode
when_to_use:
  - Passing data between Sophia (L1), Clotho (L2), and Lachesis (L3).
  - Sharing intermediate reasoning state across LangGraph nodes.
  - Broadcasting events to multiple agent listeners.
  - Coordinating parallel agent workflows.
metadata:
  audience: developers
  tier: L1-Architect
  workflow: orchestration
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
