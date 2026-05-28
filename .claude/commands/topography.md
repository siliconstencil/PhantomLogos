# Codebase Topography Analysis

Perform a structural analysis of the codebase to map dependencies and identify architectural anchors relevant to the given scope or change.

## Steps

1. **Map Current State** — Scan the target module/directory:
   - Identify all imports and exports
   - Trace call graphs (who calls what)
   - Check `last_mapped` timestamp in `.antigravity/topography.md`; if stale (>1 hr), flag for remap

2. **Identify Architectural Anchors** — Files that are central hubs (many dependents):
   - Look for files imported by 5+ other modules
   - Flag orchestrators: `src/clotho/orchestrator.py`, gateway clients in `src/architrave/`
   - Flag config and bootstrap files

3. **Downstream Dependency Map** — For the proposed change target:
   - List all files that import from it
   - List all files that are indirectly affected
   - Assign impact radius: LOCAL / MODULE / SYSTEM

4. **Side-Effect Analysis** — Predict breakage vectors:
   - Type signature changes
   - Behavioral contract changes
   - Data schema changes (Alembic migration needed?)

5. **Output**:
   - `architectural_anchors`: Core files identified
   - `downstream_dependencies`: Affected file map
   - `structural_integrity_score`: 0.0 – 1.0
   - `migration_required`: true/false
   - `recommended_context`: Files to read before making the change

## Guardrails
- Respect Sovereign Shield boundaries — do not map `.antigravity/` internal governance files.
- Only trust topographical data if files pass basic syntax check.
- Flag any circular import chains found.

Scope or change target: $ARGUMENTS
