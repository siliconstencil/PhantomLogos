"""
Mnemosyne Spatial Memory Layer (Axis 5).
SQLite-backed dependency graph for project structure queries.
Answers "which module depends on X?" and "where is this defined?"
"""

import datetime

import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)

from .models import DependencyEdge, ModuleNode, SpatialBase


class SpatialStore:
    AXIS_ID = 5

    def __init__(self, db_url: str | None = None):
        from src.utils.project_path import to_absolute_path

        db_url = db_url or f"sqlite:///{to_absolute_path('data/spatial.db')}"
        self.engine = create_engine(
            db_url, connect_args={"check_same_thread": False, "timeout": 30}
        )
        SpatialBase.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def record_dependency(self, source: str, target: str, relationship: str = "imports"):
        session = self.Session()
        try:
            existing = (
                session.query(DependencyEdge)
                .filter(
                    DependencyEdge.source_module == source,
                    DependencyEdge.target_module == target,
                )
                .first()
            )
            if not existing:
                edge = DependencyEdge(
                    source_module=source, target_module=target, relationship=relationship
                )
                session.add(edge)
                session.commit()
        except Exception as e:
            session.rollback()
            logger.error(
                f"SpatialStore (Axis {self.AXIS_ID}): record_dependency failed ({e})", exc_info=True
            )
        finally:
            session.close()

    def get_module_count(self) -> int:
        """Return number of indexed modules (for lazy indexing check)."""
        session = self.Session()
        try:
            return session.query(ModuleNode).count()
        finally:
            session.close()

    def record_module(
        self,
        module_name: str,
        file_path: str,
        line_count: int = 0,
        num_functions: int = 0,
        content_hash: str = "",
    ):
        session = self.Session()
        try:
            node = session.query(ModuleNode).filter(ModuleNode.module_name == module_name).first()
            if node:
                node.file_path = file_path
                node.line_count = line_count
                node.num_functions = num_functions
                node.content_hash = content_hash
                node.last_indexed = datetime.datetime.now(datetime.UTC)
            else:
                node = ModuleNode(
                    module_name=module_name,
                    file_path=file_path,
                    line_count=line_count,
                    num_functions=num_functions,
                    content_hash=content_hash,
                )
                session.add(node)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(
                f"SpatialStore (Axis {self.AXIS_ID}): record_module failed ({e})", exc_info=True
            )
        finally:
            session.close()

    def query_dependencies(self, module_name: str) -> list:
        """What does this module depend on?"""
        session = self.Session()
        try:
            edges = (
                session.query(DependencyEdge)
                .filter(DependencyEdge.source_module == module_name)
                .all()
            )
            return [{"module": e.target_module, "relationship": e.relationship} for e in edges]
        except Exception as e:
            logger.error(
                f"SpatialStore (Axis {self.AXIS_ID}): query_dependencies failed ({e})",
                exc_info=True,
            )
            return []
        finally:
            session.close()

    def query_dependents(self, module_name: str) -> list:
        """What depends on this module?"""
        session = self.Session()
        try:
            edges = (
                session.query(DependencyEdge)
                .filter(DependencyEdge.target_module == module_name)
                .all()
            )
            return [{"module": e.source_module, "relationship": e.relationship} for e in edges]
        except Exception as e:
            logger.error(
                f"SpatialStore (Axis {self.AXIS_ID}): query_dependents failed ({e})", exc_info=True
            )
            return []
        finally:
            session.close()

    def query_by_keywords(self, keywords: list) -> list:
        """
        Axis 5 Optimization: Perform case-insensitive SQL LIKE search.
        Eliminates the need for get_all_modules() in suggestion logic.
        """
        session = self.Session()
        try:
            query = session.query(ModuleNode)
            filters = []
            for kw in keywords:
                kw_l = f"%{kw.lower()}%"
                filters.append(
                    sa.func.lower(ModuleNode.module_name).like(kw_l)
                    | sa.func.lower(ModuleNode.file_path).like(kw_l)
                )
            if filters:
                query = query.filter(sa.or_(*filters))

            nodes = query.order_by(ModuleNode.module_name).limit(30).all()
            return [
                {
                    "name": n.module_name,
                    "path": n.file_path,
                    "lines": n.line_count,
                    "functions": n.num_functions,
                }
                for n in nodes
            ]
        except Exception as e:
            logger.error(f"SpatialStore: query_by_keywords failed ({e})")
            return []
        finally:
            session.close()

    def prune_deleted_module(self, module_name: str):
        """Removes a module and all its dependency edges (cleanup)."""
        session = self.Session()
        try:
            # Delete edges where this module is source or target
            session.query(DependencyEdge).filter(
                (DependencyEdge.source_module == module_name)
                | (DependencyEdge.target_module == module_name)
            ).delete(synchronize_session=False)

            # Delete the module itself
            session.query(ModuleNode).filter(ModuleNode.module_name == module_name).delete()

            session.commit()
            logger.info(f"SpatialStore: Pruned module '{module_name}' and its edges.")
        except Exception as e:
            session.rollback()
            logger.error(f"SpatialStore: prune_deleted_module failed ({e})")
        finally:
            session.close()

    def get_all_modules(self) -> list:
        session = self.Session()
        try:
            nodes = session.query(ModuleNode).order_by(ModuleNode.module_name).all()
            return [
                {
                    "name": n.module_name,
                    "path": n.file_path,
                    "lines": n.line_count,
                    "functions": n.num_functions,
                }
                for n in nodes
            ]
        except Exception as e:
            logger.error(
                f"SpatialStore (Axis {self.AXIS_ID}): get_all_modules failed ({e})", exc_info=True
            )
            return []
        finally:
            session.close()


if __name__ == "__main__":
    logger.info("=== Mnemosyne Spatial Store: Firmitas Test ===")
    store = SpatialStore()
    store.record_module("test_module", "src/test.py", line_count=50, num_functions=3)
    store.record_dependency("test_module", "os", "stdlib")
    deps = store.query_dependencies("test_module")
    logger.info(f"Connectivity verified. Dependencies: {deps}")
