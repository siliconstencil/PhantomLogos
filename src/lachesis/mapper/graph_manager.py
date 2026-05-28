import datetime
import json
import os
import re
import threading
from collections import defaultdict
from typing import Any, ClassVar

from src.utils.logging_config import setup_logger
from src.utils.project_path import to_absolute_path

from .ast_parser import STDLIB_MODULES, ASTParser

logger = setup_logger(__name__)

EXCLUDE_DIRS = {
    ".venv",
    ".venv-linux",
    "__pycache__",
    ".git",
    ".antigravity",
    "logs",
    "data",
    "scratch",
    "opencode_BAK",
    "opencode",
    "hermes-agent",
    "projects",
    "brain",
    ".antigravityignore",
}

_mtime_cache: dict[str, float] = {}


class CodebaseMapper:
    _lock = threading.Lock()
    _full_cache: ClassVar[dict[str, dict]] = {}

    def __init__(self, project_path: str | None = None, spatial_store: Any = None) -> None:
        from src.utils.project_path import get_project_root

        self.project_path = project_path or str(get_project_root())
        self._store = spatial_store
        self.chunk_size = int(os.getenv("MAPPER_CHUNK_SIZE", "1024"))
        self.chunk_overlap = int(os.getenv("MAPPER_CHUNK_OVERLAP", "128"))

    def _to_module_name(self, file_path: str) -> str:
        rel = os.path.relpath(file_path, self.project_path)
        rel = rel.replace("\\", "/")
        rel = re.sub(r"\.(py|json|yaml|yml|md|sql|bat|vbs)$", "", rel)
        return rel.replace("/", ".")

    def index_file(self, file_path: str, force: bool = False) -> None:
        global _mtime_cache
        try:
            current_mtime = os.path.getmtime(file_path)
        except OSError:
            return

        cached_mtime = _mtime_cache.get(file_path)
        if not force and cached_mtime is not None and abs(current_mtime - cached_mtime) < 0.1:
            return

        module_name = self._to_module_name(file_path)
        parsed = ASTParser.parse_full(file_path)

        if self._store:
            self._store.record_module(
                module_name=module_name,
                file_path=os.path.relpath(file_path, self.project_path),
                line_count=parsed["stats"]["lines"],
                num_functions=parsed["stats"]["functions"],
                content_hash=parsed["stats"]["hash"],
            )
            for target, relationship in parsed["dependencies"]:
                self._store.record_dependency(module_name, target, relationship)

        parsed["module_name"] = module_name
        CodebaseMapper._full_cache[file_path] = parsed
        _mtime_cache[file_path] = current_mtime

    def remap_file(self, file_path: str) -> None:
        if not self._store:
            return
        with self._lock:
            module_name = self._to_module_name(file_path)
            if not os.path.exists(file_path):
                self._store.prune_deleted_module(module_name)
                _mtime_cache.pop(file_path, None)
                CodebaseMapper._full_cache.pop(file_path, None)
                logger.info(f"CodebaseMapper: Pruned deleted file {file_path}")
            else:
                self.index_file(file_path, force=True)
                logger.info(f"CodebaseMapper: Incremental remap for {file_path}")

    def map_codebase(self, deep: bool = False) -> bool:
        CodebaseMapper._full_cache.clear()
        py_files = []
        for root, dirs, filenames in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            if (
                not deep
                and root != self.project_path
                and not any(k in root for k in ["src", "cognition", "scripts", "tests", "agent"])
            ):
                continue
            py_files.extend(os.path.join(root, f) for f in filenames if f.endswith(".py"))

        with self._lock:
            for file_path in py_files:
                self.index_file(file_path)
        return True

    def suggest_context(self, task_keywords: list) -> list:
        if not self._store or not task_keywords:
            return []
        with self._lock:
            matches = self._store.query_by_keywords(task_keywords)
            if not matches:
                return []
            top_matches = [m["name"] for m in matches[:3]]
            expansion = set(top_matches)
            for mod_name in top_matches:
                deps = self._store.query_dependencies(mod_name)
                for d in deps[:2]:
                    target = d.get("module")
                    if target and "." in target:
                        expansion.add(target)
            return list(expansion)

    def detect_circular(self) -> list[list[str]]:
        adj = self._build_adjacency()
        WHITE, GRAY, BLACK = 0, 1, 2  # noqa: N806
        color: dict[str, int] = {k: WHITE for k in adj}
        cycles: list[tuple[str, ...]] = []

        def dfs(node: str, path: list[str]) -> None:
            if color.get(node) != WHITE:
                return
            color[node] = GRAY
            for neigh in adj.get(node, []):
                if color.get(neigh) == GRAY:
                    if neigh in path:
                        cycle = [*path[path.index(neigh) :], neigh]
                        cycles.append(tuple(cycle))
                elif color.get(neigh) == WHITE:
                    dfs(neigh, [*path, neigh])
            color[node] = BLACK

        for node in list(adj.keys()):
            if color.get(node) == WHITE:
                dfs(node, [node])
        unique = sorted(list(set(cycles)))
        return [list(c) for c in unique]

    def _build_adjacency(self) -> dict[str, list[str]]:
        adj: dict[str, list[str]] = defaultdict(list)
        for parsed in CodebaseMapper._full_cache.values():
            src = parsed.get("module_name", "")
            for target, _ in parsed.get("dependencies", []):
                adj[src].append(target)
        if self._store:
            session = self._store.Session()
            try:
                from cognition.mnemosyne.models import DependencyEdge

                edges = session.query(DependencyEdge).all()
                for e in edges:
                    if e.target_module not in adj[e.source_module]:
                        adj[e.source_module].append(e.target_module)
            finally:
                session.close()
        return adj

    def detect_orm_models(self) -> list[dict]:
        models = [
            {
                "class": cls_info["name"],
                "bases": cls_info["bases"],
                "file": parsed.get("module_name", ""),
                "file_path": parsed.get("file", ""),
                "lineno": cls_info["lineno"],
            }
            for parsed in CodebaseMapper._full_cache.values()
            for cls_info in parsed.get("orm_models", [])
        ]
        return models

    def detect_dead_code(self) -> list[dict]:
        adj = self._build_adjacency()
        all_modules = set(adj.keys())
        imported_by: dict[str, set[str]] = defaultdict(set)
        for src, targets in adj.items():
            for tgt in targets:
                imported_by[tgt].add(src)

        dead = []
        for mod in sorted(all_modules):
            if mod.startswith("__"):
                continue
            if mod.endswith(".__init__"):
                continue
            tgt_layer = ASTParser._resolve_layer(mod)
            if tgt_layer in ("scripts", "tests"):
                continue
            if mod.startswith("alembic"):
                continue
            if mod not in imported_by or len(imported_by[mod]) == 0:
                parsed = CodebaseMapper._full_cache.get(
                    os.path.join(self.project_path, mod.replace(".", "/") + ".py")
                )
                if not parsed:
                    parsed = next(
                        (
                            p
                            for p in CodebaseMapper._full_cache.values()
                            if p.get("module_name") == mod
                        ),
                        None,
                    )
                dead.append(
                    {
                        "module": mod,
                        "imported_by": list(imported_by.get(mod, set())),
                        "line_count": (parsed or {}).get("stats", {}).get("lines", 0),
                        "functions": (parsed or {}).get("stats", {}).get("functions", 0),
                    }
                )
        return dead

    def detect_layer_violations(self) -> list[dict]:
        adj = self._build_adjacency()
        violations = []
        seen: set[tuple[str, str]] = set()
        for src, targets in adj.items():
            for tgt in targets:
                if tgt.startswith("_") or tgt.split(".")[0] in STDLIB_MODULES:
                    continue
                key = (src, tgt)
                if key in seen:
                    continue
                seen.add(key)
                is_violation, desc = ASTParser.check_layer_violation(src, tgt)
                if is_violation:
                    violations.append(
                        {
                            "source": src,
                            "target": tgt,
                            "violation": desc,
                        }
                    )
        return sorted(violations, key=lambda v: (v["source"], v["target"]))

    def generate_report(self) -> dict:
        with self._lock:
            indexed_count = sum(
                1 for p in CodebaseMapper._full_cache.values() if p.get("module_name")
            )
            total_lines = sum(
                p.get("stats", {}).get("lines", 0) for p in CodebaseMapper._full_cache.values()
            )
            total_funcs = sum(
                p.get("stats", {}).get("functions", 0) for p in CodebaseMapper._full_cache.values()
            )
            circular = self.detect_circular()
            orm_models = self.detect_orm_models()
            dead_code = self.detect_dead_code()
            layer_violations = self.detect_layer_violations()

            modules = []
            for parsed in sorted(
                CodebaseMapper._full_cache.values(),
                key=lambda p: p.get("module_name", ""),
            ):
                mod_name = parsed.get("module_name", "")
                if not mod_name:
                    continue
                dependencies = [
                    {"target": tgt, "type": rel} for tgt, rel in parsed.get("dependencies", [])
                ]
                modules.append(
                    {
                        "module": mod_name,
                        "axis": ASTParser._resolve_axis(mod_name),
                        "file": parsed.get("file", ""),
                        "stats": parsed.get("stats", {}),
                        "dependencies": dependencies,
                        "classes": parsed.get("classes", []),
                        "functions": parsed.get("functions", []),
                        "orm_models": [
                            {"class": c["name"], "bases": c["bases"]}
                            for c in parsed.get("orm_models", [])
                        ],
                    }
                )

            dependents: dict[str, list[str]] = defaultdict(list)
            for m in modules:
                for dep in m["dependencies"]:
                    dependents[dep["target"]].append(m["module"])

            for m in modules:
                m["dependents"] = sorted(set(dependents.get(m["module"], [])))

            report = {
                "generated_at": datetime.datetime.now(datetime.UTC).isoformat() + "Z",
                "project_root": self.project_path,
                "summary": {
                    "total_modules": indexed_count,
                    "total_lines": total_lines,
                    "total_functions": total_funcs,
                    "total_dependencies": sum(len(m["dependencies"]) for m in modules),
                    "circular_dependencies": len(circular),
                    "orm_models": len(orm_models),
                    "dead_code_modules": len(dead_code),
                    "layer_violations": len(layer_violations),
                },
                "circular_dependencies": [{"cycle": c, "length": len(c)} for c in circular],
                "orm_models": orm_models,
                "dead_code": dead_code,
                "layer_violations": layer_violations,
                "modules": modules,
            }

            return report

    def write_report(self, output_path: str | None = None) -> str:
        report = self.generate_report()
        output_path = output_path or to_absolute_path("logs/mapper_report.json")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)
        logger.info(f"Mapper report written to {output_path}")
        return output_path
