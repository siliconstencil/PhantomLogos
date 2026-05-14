import os
import re
import threading
from collections import defaultdict

from src.utils.logging_config import setup_logger

from .ast_parser import ASTParser

logger = setup_logger(__name__)

EXCLUDE_DIRS = {
    ".venv",
    "__pycache__",
    ".git",
    ".antigravity",
    "logs",
    "data",
    "scratch",
    "opencode_BAK",
    "opencode",
    "hermes-agent",
}

# Shared caches
_mtime_cache = {}
_scanned_patterns = set()


class CodebaseMapper:
    _lock = threading.Lock()

    def __init__(self, project_path: str | None = None, spatial_store=None):
        from src.utils.project_path import get_project_root

        self.project_path = project_path or str(get_project_root())
        self._store = spatial_store
        # [SRC:axis_5] Context hardening attributes for RAG alignment.
        self.chunk_size = int(os.getenv("MAPPER_CHUNK_SIZE", "1024"))
        self.chunk_overlap = int(os.getenv("MAPPER_CHUNK_OVERLAP", "128"))

    def _to_module_name(self, file_path: str) -> str:
        rel = os.path.relpath(file_path, self.project_path)
        rel = rel.replace("\\", "/")
        rel = re.sub(r"\.(py|json|yaml|yml|md|sql|bat|vbs)$", "", rel)
        return rel.replace("/", ".")

    def index_file(self, file_path: str, force: bool = False):
        global _mtime_cache
        try:
            current_mtime = os.path.getmtime(file_path)
        except OSError:
            return

        cached_mtime = _mtime_cache.get(file_path)
        if not force and cached_mtime is not None and abs(current_mtime - cached_mtime) < 0.1:
            return

        module_name = self._to_module_name(file_path)
        stats = ASTParser.get_file_stats(file_path)
        self._store.record_module(
            module_name=module_name,
            file_path=os.path.relpath(file_path, self.project_path),
            line_count=stats["lines"],
            num_functions=stats["functions"],
            content_hash=stats["hash"],
        )
        deps = ASTParser.parse_dependencies(file_path)
        for target, relationship in deps:
            self._store.record_dependency(module_name, target, relationship)
        _mtime_cache[file_path] = current_mtime

    def remap_file(self, file_path: str):
        if not self._store:
            return
        with self._lock:
            module_name = self._to_module_name(file_path)
            if not os.path.exists(file_path):
                self._store.prune_deleted_module(module_name)
                _mtime_cache.pop(file_path, None)
                logger.info(f"CodebaseMapper: Pruned deleted file {file_path}")
            else:
                self.index_file(file_path, force=True)
                logger.info(f"CodebaseMapper: Incremental remap for {file_path}")

    def map_codebase(self, deep: bool = False) -> bool:
        if not self._store:
            return False
        with self._lock:
            py_files = []
            for root, dirs, files in os.walk(self.project_path):
                dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
                if (
                    not deep
                    and root != self.project_path
                    and not any(
                        k in root for k in ["src", "cognition", "scripts", "tests", "agent"]
                    )
                ):
                    continue
                for f in files:
                    if f.endswith(".py"):
                        py_files.append(os.path.join(root, f))
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

    def detect_circular(self) -> list:
        if not self._store:
            return []
        with self._lock:
            adj = defaultdict(list)
            session = self._store.Session()
            try:
                from cognition.mnemosyne.spatial_store import DependencyEdge

                edges = session.query(DependencyEdge).all()
                for e in edges:
                    adj[e.source_module].append(e.target_module)
            finally:
                session.close()

            WHITE, GRAY, BLACK = 0, 1, 2
            color = {k: WHITE for k in adj}
            cycles = []

            def dfs(node, path):
                color[node] = GRAY
                for neigh in adj.get(node, []):
                    if color.get(neigh) == GRAY:
                        if neigh in path:
                            cycle = path[path.index(neigh) :] + [neigh]
                            cycles.append(tuple(cycle))
                    elif color.get(neigh) == WHITE:
                        dfs(neigh, path + [neigh])
                color[node] = BLACK

            for node in list(adj.keys()):
                if color.get(node) == WHITE:
                    dfs(node, [node])

            unique_cycles = sorted(list(set(cycles)))
            return [list(c) for c in unique_cycles]
