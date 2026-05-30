from src.lachesis.mapper.ast_parser import ASTParser
from src.lachesis.mapper.graph_manager import CodebaseMapper


def test_axis_mapping_logic():
    # Test specific module names
    assert ASTParser._resolve_axis("cognition.mnemosyne.write_path") == 1
    assert ASTParser._resolve_axis("src.clotho.orchestrator") == 2
    assert ASTParser._resolve_axis("src.lachesis.mapper.graph_manager") == 5
    assert ASTParser._resolve_axis("src.clotho.ergon.synergeia") == 6
    assert ASTParser._resolve_axis("src.utils.logging_config") == 7
    assert ASTParser._resolve_axis("alembic.env") == 13
    assert ASTParser._resolve_axis("random_module") is None
    print("\n[SUCCESS] Axis mapping logic verified.")


def test_mapper_report_axis():
    mapper = CodebaseMapper()
    # Fake index some core files if not already cached
    import os
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_file = os.path.join(project_root, "src", "clotho", "orchestrator.py")
    mapper.index_file(target_file, force=True)
    report = mapper.generate_report()

    found_axis = False
    for mod in report["modules"]:
        if mod["module"] == "src.clotho.orchestrator":
            assert mod["axis"] == 2
            found_axis = True
            break

    assert found_axis, "Could not find src.clotho.orchestrator in report"
    print("[SUCCESS] Mapper report contains Axis labels.")


if __name__ == "__main__":
    test_axis_mapping_logic()
    test_mapper_report_axis()
