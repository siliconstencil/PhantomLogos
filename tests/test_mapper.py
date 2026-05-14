import os
from unittest.mock import MagicMock

import pytest

# PYTHONPATH is handled by conftest.py and environment
from src.lachesis.mapper import ASTParser, CodebaseMapper


def test_ast_parser_dependency_extraction():
    # Create a dummy file for testing
    test_file = "scratch/dummy_test_module.py"
    os.makedirs("scratch", exist_ok=True)
    with open(test_file, "w") as f:
        f.write("import os\n")
        f.write("from cognition.mnemosyne.spatial_store import SpatialStore\n")
        f.write("def test_func():\n    pass\n")

    deps = ASTParser.parse_dependencies(test_file)
    dep_targets = [d[0] for d in deps]

    assert "os" in dep_targets
    assert "cognition.mnemosyne.spatial_store" in dep_targets

    stats = ASTParser.get_file_stats(test_file)
    assert stats["lines"] >= 3
    assert stats["functions"] == 1

    os.remove(test_file)


def test_codebase_mapper_index_file():
    # Mock SpatialStore
    mock_store = MagicMock()
    mapper = CodebaseMapper(spatial_store=mock_store)

    test_file = "scratch/dummy_mapper_test.py"
    with open(test_file, "w") as f:
        f.write("import sys\n")

    # We need to use absolute path for index_file logic
    abs_path = os.path.abspath(test_file)
    mapper.index_file(abs_path, force=True)

    # Verify store calls
    assert mock_store.record_module.called
    assert mock_store.record_dependency.called

    os.remove(test_file)


def test_circular_dependency_detection():
    # Mock SpatialStore with circular edges
    mock_store = MagicMock()
    # We need a real session mock for detect_circular
    mock_session = MagicMock()
    mock_store.Session.return_value = mock_session

    from cognition.mnemosyne.spatial_store import DependencyEdge

    edge1 = DependencyEdge(source_module="A", target_module="B", relationship="import")
    edge2 = DependencyEdge(source_module="B", target_module="A", relationship="import")

    mock_session.query.return_value.all.return_value = [edge1, edge2]

    mapper = CodebaseMapper(spatial_store=mock_store)
    cycles = mapper.detect_circular()

    assert len(cycles) > 0
    # One of the cycles should be ['A', 'B', 'A'] or ['B', 'A', 'B']
    cycle_nodes = set(cycles[0])
    assert "A" in cycle_nodes
    assert "B" in cycle_nodes


if __name__ == "__main__":
    pytest.main([__file__])
