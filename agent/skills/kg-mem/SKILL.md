---
name: kg-mem
description: Knowledge Graph memory via MCP. Stores and queries structured entities and relations in a persistent JSON knowledge graph.
version: 1.0.0
license: MIT
compatibility: opencode
model_role: expert
allowed_tools:
  - kg-mem_create_entities
  - kg-mem_create_relations
  - kg-mem_add_observations
  - kg-mem_search_nodes
  - kg-mem_open_nodes
  - kg-mem_read_graph
  - kg-mem_delete_entities
  - kg-mem_delete_observations
  - kg-mem_delete_relations
  - mcp_slm_recall
  - semantic
tier: 3
when_to_use:
  - Building structured knowledge about project entities and their relations.
  - Long-term memory that persists across sessions beyond SLM context.
  - Cross-referencing domain concepts with codebase entities.
  - Mapping relationships between components, APIs, and business logic.
metadata:
  audience: developers
  tier: L3-Auditor
  workflow: memory
---

# Skill: Knowledge Graph Memory

Structured entity-relation knowledge graph that persists across sessions. Complements Mnemosyne Axis 6 (semantic vector search) with explicit graph relationships.

## Relation to Mnemosyne

| System | Storage | Query | Best For |
|--------|---------|-------|----------|
| SLM | Vector DB | Semantic recall | Episodic/procedural memory |
| Mnemosyne Axis 6 | LanceDB + FTS | Hybrid search | Code semantics |
| **KG-Mem** | **JSON graph** | **Graph traversal** | **Structured entities + relations** |

KG-Mem fills the gap: explicit entity-relation graphs that vector search cannot provide.

## Available Tools

| Tool | Description |
|------|-------------|
| `kg-mem_create_entities` | Bulk create entities with name, type, observations |
| `kg-mem_create_relations` | Bulk create relations between entities |
| `kg-mem_add_observations` | Add observations to existing entities |
| `kg-mem_search_nodes` | Full-text search across entity names/types |
| `kg-mem_open_nodes` | Get full details for specific entity names |
| `kg-mem_read_graph` | Export full knowledge graph |
| `kg-mem_delete_entities` | Remove entities by name |
| `kg-mem_delete_observations` | Remove specific observations |
| `kg-mem_delete_relations` | Remove relations by pattern |

## Workflow

1. **Extract**: After reading code/docs, extract key entities (components, APIs, concepts)
2. **Connect**: Add relations between entities (depends_on, implements, extends, configured_by)
3. **Query**: Use graph traversal for cross-cutting questions
4. **Maintain**: Update as codebase evolves

## Entity Schema

```json
{
  "name": "PaymentService",
  "entityType": "service",
  "observations": ["Handles payment processing via Stripe", "Called by CheckoutController"]
}
```

## Relation Schema

```json
{
  "from": "PaymentService",
  "relationType": "depends_on",
  "to": "StripeAPI"
}
```

## Guardrails

- DO NOT store secrets, API keys, or credentials in KG (it's a JSON file)
- Keep entity names consistent (use fully qualified names where possible)
- Prefer `depends_on`, `implements`, `extends`, `configured_by`, `triggers` as relation types
- Periodically prune stale entities as codebase evolves
