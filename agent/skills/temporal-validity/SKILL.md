---
name: temporal-validity
description: Time-respecting memory retrieval with event_key supersede lifecycle and
  fact history on Axis 4.
version: 1.0.0
license: MIT
compatibility: opencode
model_role: light
allowed_tools:
- semantic
- mcp_slm_context
- verify
tier: 1
---
# Temporal Validity

Enforces temporal correctness through event_key lifecycle and point-in-time fact queries.

## Core Concepts

### event_key Lifecycle
- `record()` Creates a new temporal entry with an event_key.
- `get_fact_at(key, timestamp)` Retrieves the state of a fact as of a given time.
- `supersede(key)` Marks an entry as superseded (soft-delete with history preservation).

### TemporalStore (Axis 4)
- Time-series metrics for operation latency and event sequences.
- Singleton initialization to prevent redundant schema creation.
- Enables historical analysis across sessions.

## Best Practices
- Always use `get_fact_at()` for time-sensitive decisions.
- Use `supersede()` instead of `delete()` to preserve audit trail.
- Reference [SRC:axis_4] when citing temporal data.
