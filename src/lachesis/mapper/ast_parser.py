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


class ASTParser:
    @staticmethod
    def parse_dependencies(file_path: str) -> list[tuple]:
        dependencies = []
        if not os.path.exists(file_path):
            return dependencies

        if not file_path.endswith(".py"):
            return ASTParser._parse_config_refs(file_path)

        try:
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                tree = ast.parse(f.read())

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        dependencies.append((alias.name, ASTParser._classify_module(alias.name)))
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        dependencies.append((node.module, ASTParser._classify_module(node.module)))
        except Exception as e:
            logger.error(f"Lachesis: AST Parse failed for {file_path} ({e})")

        return dependencies

    @staticmethod
    def _parse_config_refs(file_path: str) -> list[tuple]:
        return []

    @staticmethod
    def _classify_module(target: str) -> str:
        top_level = target.split(".")[0]
        if top_level in STDLIB_MODULES:
            return "stdlib"
        elif top_level.startswith("_"):
            return "internal"
        return "project"

    @staticmethod
    def get_file_stats(file_path: str) -> dict:
        try:
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                content = f.read()

            lines = content.count("\n") + 1
            num_defs = 0
            if file_path.endswith(".py"):
                try:
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                            num_defs += 1
                except Exception as e:
                    logger.debug(f"ASTParser: parse failed for {file_path} ({e})")
                    pass

            content_hash = hashlib.md5(content.encode("utf-8")).hexdigest()[:16]
            return {"lines": lines, "functions": num_defs, "hash": content_hash}
        except Exception as e:
            logger.debug(f"ASTParser: stats failed for {file_path} ({e})")
            return {"lines": 0, "functions": 0, "hash": ""}
