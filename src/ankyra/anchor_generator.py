import json

from cognition.mnemosyne.rational_store import MnemosyneRationalStore
from cognition.mnemosyne.spatial_store import SpatialStore
from src.utils.project_path import get_project_root

from ..lachesis import CodebaseMapper


class AnchorGenerator:
    """
    Ankyra Anchor Context Generator.
    Consolidates rules, facts, and codebase mapping into a persistent anchor document.
    Uses Lachesis (SpatialStore) for codebase graph, not raw os.walk.
    """

    def __init__(self):
        self.rational_store = MnemosyneRationalStore()
        self._spatial = SpatialStore()
        self.mapper = CodebaseMapper(
            project_path=str(get_project_root()), spatial_store=self._spatial
        )

    def generate_atomic_anchors(self):
        """Generates atomic anchor fragments and stores them in Axis 12 ContextCache."""
        print("Generating Ankyra Atomic Anchors...")

        from src.architrave.context_cache import AnchorContextBuilder, ContextCacheStore

        builder = AnchorContextBuilder()
        cache = ContextCacheStore()

        # 1. Governance Fragment
        rules = self.rational_store.get_secure_rules(agent_id="system")
        rules_md = "\n".join([f"- [{r['id']}] {r['desc']}" for r in rules])
        builder.add_fragment("governance_rules", rules_md, axis=10, precedence=200)

        # 2. Project State Fragment
        facts = "Project: Antigravity\nStatus: Phase 11 - Managed Agentic OS (SOTA 2026)"
        builder.add_fragment("project_state", facts, axis=3, precedence=150)

        # 3. Codebase Fragments (Module-based)
        self.mapper.map_codebase(deep=False)
        modules = self._spatial.get_all_modules()
        for m in modules:
            content = f"Module: {m['name']}\nPath: {m['path']}\nFunctions: {m['functions']}"
            builder.add_fragment(f"module_{m['name']}", content, axis=5, precedence=100)

        # Save to ContextCache (Axis 12 SSD)
        for frag in builder.fragments:
            cache.set(json.dumps(frag), ttl_seconds=86400)  # 24h TTL

        print(f"Generated {len(builder.fragments)} atomic anchors in Axis 12.")

    def _get_codebase_summary(self) -> str:
        """Generate codebase summary from SpatialStore data."""
        modules = self._spatial.get_all_modules()
        if not modules:
            return "(no modules indexed)"

        lines = []
        for m in sorted(modules, key=lambda x: x["name"]):
            deps = self._spatial.query_dependencies(m["name"])
            dep_names = ", ".join(d["module"] for d in deps[:5])
            if len(deps) > 5:
                dep_names += f" ... (+{len(deps) - 5})"
            lines.append(f"  - {m['name']} ({m['path']}, {m['functions']} funcs)")
            if dep_names:
                lines.append(f"      depends on: {dep_names}")
        return "\n".join(lines)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--force":
        generator = AnchorGenerator()
        generator.generate_atomic_anchors()
    else:
        print("Usage: python anchor_generator.py --force (to generate atomic anchors)")
