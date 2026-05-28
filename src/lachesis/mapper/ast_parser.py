import ast
import hashlib
import os

from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)

STDLIB_MODULES = {
    "os",
    "sys",
    "re",
    "json",
    "math",
    "time",
    "datetime",
    "typing",
    "collections",
    "functools",
    "pathlib",
    "hashlib",
    "subprocess",
    "threading",
    "asyncio",
    "abc",
    "copy",
    "enum",
    "io",
    "itertools",
    "logging",
    "random",
    "statistics",
    "string",
    "textwrap",
    "uuid",
    "warnings",
    "weakref",
    "inspect",
    "dataclasses",
}

KNOWN_ORM_BASES = {
    "Base",
    "MnemosyneBase",
    "SpatialBase",
    "ReliabilityBase",
    "DeclarativeBase",
    "declarative_base",
}

LAYER_RULES = {
    "cognition.mnemosyne": {"allow": ["src.utils", "cognition.mnemosyne", "src.architrave"]},
    "cognition.sophia": {
        "allow": [
            "src.utils",
            "cognition.mnemosyne",
            "src.architrave",
            "src.lachesis",
            "src.clotho",
            "scripts",
            "cognition.morpheus",
        ]
    },
    "cognition.morpheus": {
        "allow": ["src.utils", "cognition.mnemosyne", "src.muscle", "src.architrave", "src.clotho"]
    },
    "src.clotho": {
        "allow": [
            "src.utils",
            "cognition.sophia",
            "cognition.mnemosyne",
            "src.architrave",
            "src.lachesis",
            "src.muscle",
            "src.tools",
            "src.clotho",
            "cognition.morpheus",
        ]
    },
    "src.lachesis": {
        "allow": [
            "src.utils",
            "cognition.mnemosyne",
            "src.architrave",
            "src.lachesis",
            "src.clotho",
            "cognition.morpheus",
        ]
    },
    "src.architrave": {
        "allow": ["src.utils", "cognition.mnemosyne", "cognition.sophia", "src.lachesis"]
    },
    "src.muscle": {"allow": ["src.utils", "src.architrave"]},
    "src.utils": {"allow": ["cognition.mnemosyne", "cognition.morpheus", "src.lachesis"]},
    "src.tools": {"allow": ["src.utils"]},
    "scripts": {"allow": ["src.utils", "cognition", "src"]},
    "tests": {"allow": ["src", "cognition", "scripts"]},
}


class ASTParser:
    @staticmethod
    def parse_full(file_path: str) -> dict:
        result = {
            "file": file_path,
            "dependencies": [],
            "classes": [],
            "functions": [],
            "imports": [],
            "orm_models": [],
            "stats": {"lines": 0, "functions": 0, "hash": ""},
        }
        if not os.path.exists(file_path):
            return result
        if not file_path.endswith(".py"):
            return result

        try:
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                content = f.read()

            tree = ast.parse(content)
            result["stats"] = ASTParser._compute_stats(content, tree)
            result["dependencies"] = ASTParser._extract_deps(tree, file_path)
            result["classes"] = ASTParser._extract_classes(tree)
            result["functions"] = ASTParser._extract_functions(tree)
            result["imports"] = ASTParser._extract_imports(tree)
            result["orm_models"] = [
                c for c in result["classes"] if any(b in KNOWN_ORM_BASES for b in c["bases"])
            ]
        except SyntaxError as e:
            logger.warning(f"ASTParser: syntax error in {file_path}: {e}")
        except Exception as e:
            logger.error(f"ASTParser: parse_full failed for {file_path} ({e})")

        return result

    @staticmethod
    def parse_dependencies(file_path: str) -> list[tuple]:
        result = ASTParser.parse_full(file_path)
        return result["dependencies"]

    @staticmethod
    def get_file_stats(file_path: str) -> dict:
        result = ASTParser.parse_full(file_path)
        return result["stats"]

    @staticmethod
    def _extract_deps(tree: ast.Module, file_path: str = "") -> list[tuple]:
        deps = []
        module_name = ASTParser._file_to_module(file_path) if file_path else ""
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                deps.extend(
                    (alias.name, ASTParser._classify_module(alias.name)) for alias in node.names
                )
            elif isinstance(node, ast.ImportFrom):
                resolved = ASTParser._resolve_import(module_name, node)
                if resolved:
                    deps.append((resolved, ASTParser._classify_module(resolved)))
        return deps

    @staticmethod
    def _file_to_module(file_path: str) -> str:
        from src.utils.project_path import get_project_root

        root = str(get_project_root())
        rel = os.path.relpath(file_path, root).replace("\\", "/")
        rel = rel[:-3] if rel.endswith(".py") else rel
        return rel.replace("/", ".")

    @staticmethod
    def _resolve_import(module_name: str, node: ast.ImportFrom) -> str | None:
        if node.level == 0:
            return node.module
        if not module_name:
            return node.module
        parts = module_name.split(".")
        pkg_parts = parts[:-1]
        level = node.level
        if level > len(pkg_parts) + 1:
            return node.module
        base = pkg_parts[: -(level - 1)] if level > 1 else pkg_parts
        if node.module:
            return ".".join(base + node.module.split("."))
        return ".".join(base)

    @staticmethod
    def _extract_classes(tree: ast.Module) -> list[dict]:
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                bases = []
                for base in node.bases:
                    if isinstance(base, ast.Attribute):
                        bases.append(base.attr)
                    elif isinstance(base, ast.Name):
                        bases.append(base.id)
                    elif isinstance(base, ast.Call) and isinstance(base.func, ast.Name):
                        bases.append(base.func.id)
                classes.append(
                    {
                        "name": node.name,
                        "bases": bases,
                        "lineno": node.lineno,
                        "num_methods": sum(
                            1
                            for n in ast.walk(node)
                            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                        ),
                    }
                )
        return classes

    @staticmethod
    def _extract_functions(tree: ast.Module) -> list[dict]:
        funcs = [
            {
                "name": node.name,
                "lineno": node.lineno,
                "is_async": isinstance(node, ast.AsyncFunctionDef),
            }
            for node in ast.iter_child_nodes(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        return funcs

    @staticmethod
    def _extract_imports(tree: ast.Module) -> list[dict]:
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(
                    {"module": alias.name, "alias": alias.asname, "lineno": node.lineno}
                    for alias in node.names
                )
            elif isinstance(node, ast.ImportFrom):
                imports.append(
                    {
                        "module": node.module or "",
                        "names": [a.name for a in node.names],
                        "level": node.level,
                        "lineno": node.lineno,
                    }
                )
        return imports

    @staticmethod
    def _compute_stats(content: str, tree: ast.Module) -> dict:
        lines = content.count("\n") + 1
        num_defs = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                num_defs += 1
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]
        return {"lines": lines, "functions": num_defs, "hash": content_hash}

    @staticmethod
    def _classify_module(target: str) -> str:
        top_level = target.split(".")[0]
        if top_level in STDLIB_MODULES:
            return "stdlib"
        if top_level.startswith("_"):
            return "internal"
        return "project"

    @staticmethod
    def check_layer_violation(source_module: str, target_module: str) -> tuple[bool, str]:
        if not target_module or target_module.startswith("_"):
            return False, ""
        top = target_module.split(".")[0]
        if top in STDLIB_MODULES:
            return False, ""

        src_layer = ASTParser._resolve_layer(source_module)
        tgt_layer = ASTParser._resolve_layer(target_module)

        if not src_layer or not tgt_layer:
            return False, ""

        if src_layer == tgt_layer:
            return False, ""

        allowed = LAYER_RULES.get(src_layer, {}).get("allow", [])
        for prefix in allowed:
            if tgt_layer == prefix or tgt_layer.startswith(prefix + "."):
                return False, ""
        return True, f"{src_layer} -> {tgt_layer}"

    @staticmethod
    def _resolve_layer(module_name: str) -> str:
        for prefix in [
            "cognition.mnemosyne",
            "cognition.sophia",
            "cognition.morpheus",
            "src.clotho",
            "src.lachesis",
            "src.architrave",
            "src.muscle",
            "src.utils",
            "src.tools",
            "scripts",
            "tests",
        ]:
            if module_name == prefix or module_name.startswith(prefix + "."):
                return prefix
        return ""

    @staticmethod
    def _resolve_axis(module_name: str) -> int | None:
        """SSOT: Map modules to Mnemosyne Axis (1-14)."""
        mapping = {
            "cognition.mnemosyne.write_path": 1,
            "cognition.mnemosyne.models": 1,
            "src.clotho.orchestrator": 2,
            "src.clotho.ergon": 2,
            "cognition.mnemosyne.goal_store": 3,
            "cognition.mnemosyne.temporal_store": 4,
            "src.lachesis.mapper": 5,
            "src.clotho.ergon.synergeia": 6,
            "cognition.mnemosyne.operational_store": 7,
            "src.utils.logging_config": 7,
            "src.lachesis.self_tuner": 8,
            "src.architrave.verify": 11,
            "src.clotho.ergon.verify": 11,
            "alembic": 13,
            "cognition.mnemosyne.session": 13,
        }
        # Sort by length descending to match most specific prefix first
        sorted_prefixes = sorted(mapping.keys(), key=len, reverse=True)
        for prefix in sorted_prefixes:
            if module_name == prefix or module_name.startswith(prefix + "."):
                return mapping[prefix]
        return None
