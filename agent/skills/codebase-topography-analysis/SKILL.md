---
name: codebase-topography-analysis
description: Advanced structural analysis of the codebase via AST mapping and dependency graph querying.
version: 1.0.0
license: MIT
compatibility: opencode
when_to_use:
  - Planning structural refactoring or directory migration.
  - Identifying the side-effects of changing a core utility.
  - Mapping the system's cognitive topography for JIT context assembly.
metadata:
  audience: architects
  tier: L1-Sophia
  workflow: codebase-mapping
---
# Skill: Codebase Topography Analysis (Mapper+)

Goes beyond simple file listing by analyzing the system's structural "terrain" to predict dependencies and identify critical architectural nodes.

## Workflow
1.  **Map**: Call the `mapper` tool to update the `SpatialStore` (Axis 5) with current file/directory states.
2.  **Query Graph**: Use SQL or semantic queries on the `spatial.db` to identify downstream dependencies of a target module.
3.  **Identify Critical Nodes**: Pin files that are "Architectural Anchors" (e.g., `fs.py`, `project_path.py`, `meta_cognition.py`).
4.  **Side-Effect Analysis**: Predict how a change in a leaf node might affect high-level orchestration or data flow.
5.  **Context Assembly**: Select only the most relevant "topographical" neighbors for injection into the reasoning context.

## Guardrails
- **Stale Data**: Always check the `last_mapped` timestamp in Axis 5; if > 1 hour, trigger a background remap.
- **AST Integrity**: Only trust topographical data if the files pass a basic syntax (compile-check) audit.
- **Isolation**: When analyzing topography, respect the "Sovereign Shield" boundaries; do not attempt to map restricted system directories.

## Output Format
- `architectural_anchors`: List of core files identified in the current scope.
- `downstream_dependencies`: Map of files affected by the proposed change.
- `structural_integrity_score`: Score (0.0 - 1.0) of the current codebase topography.
- `topographical_neighbors`: List of files suggested for context injection.
