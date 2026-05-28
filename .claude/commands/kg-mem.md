# Knowledge Graph Memory

Build and query structured entity-relation knowledge using kg-mem MCP. Persists across sessions.

## When to Use

- Map relationships between project components (depends_on, implements, extends).
- Track architectural decisions and their rationale as queryable entities.
- Cross-reference domain concepts with codebase entities.
- Complement SLM (episodic recall) with explicit graph structure.

## Workflow

### Build Knowledge
```
1. Extract entities from code/docs (components, APIs, services, concepts)
2. create_entities([{name, entityType, observations}])
3. create_relations([{from, relationType, to}])
4. add_observations for updates as codebase evolves
```

### Query Knowledge
```
search_nodes(query) -> find entities by name or type
open_nodes([names]) -> get full entity details
read_graph() -> export full graph (use sparingly)
```

### Maintain
```
delete_observations -> remove stale facts
delete_relations -> remove outdated links
delete_entities -> remove obsolete components
```

## Entity Schema

```json
{"name": "GatewayArchitrave", "entityType": "module", "observations": ["Central LLM routing layer", "Reads mcp_config.json"]}
```

## Relation Types

Prefer: `depends_on`, `implements`, `extends`, `configured_by`, `triggers`, `calls`, `reads_from`, `writes_to`

## Guardrails
- NEVER store API keys, tokens, or secrets (JSON file, not encrypted).
- Keep entity names consistent — use fully qualified module paths.
- Prune stale entities after major refactors.

Operation or query: $ARGUMENTS
