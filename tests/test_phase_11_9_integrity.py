import os

import pytest
import yaml


# [SRC:axis_10]
def test_governance_files():
    files = ["AGENTS.md", "GEMINI.md", ".cursorrules"]
    for f in files:
        path = f
        assert os.path.exists(path), f"{f} missing"
        with open(path, encoding="utf-8") as file:
            content = file.read()
            assert "11.9" in content or "11.8" in content or "v1.0.0" in content, (
                f"{f} version mismatch"
            )


def test_agent_yamls():
    agents = ["sophia.yaml", "clotho.yaml", "lachesis.yaml"]
    for a in agents:
        path = os.path.join("agent", a)
        assert os.path.exists(path), f"{a} missing"
        with open(path) as f:
            cfg = yaml.safe_load(f)
            assert "tier_config" in cfg, f"{a} missing tier_config"
            assert "response_format" in cfg, f"{a} missing response_format"


def test_hermes_tools():
    path = os.path.join("agent", "hermes.yaml")
    assert os.path.exists(path)
    with open(path) as f:
        cfg = yaml.safe_load(f)
        assert len(cfg.get("tools", [])) >= 5


def test_ascii_audit():
    path = "src/muscle/local_runtime.py"
    if not os.path.exists(path):
        pytest.skip("local_runtime.py not found")
    with open(path, encoding="utf-8") as f:
        content = f.read()
        turkish_chars = "\u00e7\u011f\u0131\u015f\u00f6\u00fc\u00c7\u011e\u0130\u015e\u00d6\u00dc"
        for char in turkish_chars:
            assert char not in content, f"Turkish character '{char}' found in {path}"


def test_db_pruning_logic():
    path = "cognition/morpheus/sweeper.py"
    assert os.path.exists(path)
    with open(path, encoding="utf-8") as f:
        content = f.read()
        assert "spatial.db" in content or "mnemosyne.db" in content
        assert "WAL" in content


def test_lancedb_optimization():
    files = ["cognition/mnemosyne/semantic_store.py", "cognition/mnemosyne/temporal_store.py"]
    for f in files:
        if not os.path.exists(f):
            continue
        with open(f, encoding="utf-8") as file:
            assert "cleanup" in file.read().lower()


def test_pip_cleanup():
    try:
        import google.generativeai

        pytest.fail("google-generativeai still installed")
    except ImportError:
        pass
