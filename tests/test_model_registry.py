import pytest

from src.architrave.model_registry import (
    VRAM_CATALOG_GB,
    get_embedding_model,
    get_qwed_models,
    resolve_local_model,
)


def test_vision_resolution():
    model = resolve_local_model("vision")
    assert model == "mimo-vl:latest"

    variant = resolve_local_model("vision", "thinking")
    assert variant == "mimo-vl:latest"


def test_vram_catalog():
    assert "mimo-vl:latest" in VRAM_CATALOG_GB
    assert VRAM_CATALOG_GB["mimo-vl:latest"] == 5.7
    assert "deepseek-math:7b" in VRAM_CATALOG_GB
    assert VRAM_CATALOG_GB["deepseek-math:7b"] == 4.7


def test_embedding_helpers():
    assert get_embedding_model() == "nomic-embed-text-v2-moe-q8:latest"
    assert get_embedding_model("quality") == "nomic-embed-text-v2-moe-q16:latest"


def test_qwed_config():
    config = get_qwed_models()
    assert config["primary"] == "qwen2-5-coder-3b-instruct-q6_k:latest"
    assert config["fallback"] == "functiongemma-270m-it-q8_0:latest"


def test_bridge_resolution():
    from src.clotho.bridge.base import ToolBridge

    bridge = ToolBridge(session_id="test")
    # Test shorthand resolution
    assert bridge._resolve_model("qwen-7b") == "qwen2-5-coder-7b-instruct-q4_k_m:latest"
    # Test registry-based resolution
    assert bridge._resolve_model("vision") == "mimo-vl:latest"


if __name__ == "__main__":
    pytest.main([__file__])
