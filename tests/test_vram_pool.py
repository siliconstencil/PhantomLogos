import time
from unittest.mock import MagicMock, patch

import pytest

from cognition.morpheus.loader import KeepAlivePool, ModelLoader, VRAMBudgetGuard
from cognition.morpheus.scheduler import MorpheusScheduler


@pytest.fixture
def mock_loader():
    with patch("ollama.Client") as mock_client:
        loader = ModelLoader(base_url="http://localhost:11434")
        loader.base_url = "http://localhost:11434"
        yield loader


@pytest.mark.asyncio
async def test_keep_alive_pool_lru():
    pool = KeepAlivePool(max_size=2)
    # Add 2 models
    pool.add("model_a")
    time.sleep(0.01)
    pool.add("model_b")
    assert pool.size() == 2
    assert pool.contains("model_a")
    assert pool.contains("model_b")

    # LRU model should be model_a
    lru = pool.get_least_recently_used()
    assert lru == "model_a"

    # Touch model_a to make model_b LRU
    pool.add("model_a")
    lru = pool.get_least_recently_used()
    assert lru == "model_b"


@pytest.mark.asyncio
async def test_core_models_never_evicted():
    pool = KeepAlivePool(max_size=2)
    pool.add("tinyllama:latest")  # core model
    time.sleep(0.01)
    pool.add("model_a")

    # LRU should skip tinyllama and return model_a
    lru = pool.get_least_recently_used()
    assert lru == "model_a"


@pytest.mark.asyncio
async def test_vram_budget_guard_success():
    guard = VRAMBudgetGuard(min_free_gb=1.0)
    loader = MagicMock()
    loader._loaded_model = None
    loader._pool = KeepAlivePool(max_size=2)

    with patch("cognition.morpheus.monitor.get_gpu_memory_info") as mock_vram:
        mock_vram.return_value = {"free_gb": 4.0}
        # Required is 2.0GB, we have 4.0GB, min is 1.0GB. 4.0 - 2.0 = 2.0 >= 1.0 -> should pass without eviction!
        assert guard.guard_vram(2.0, loader) is True


@pytest.mark.asyncio
async def test_vram_budget_guard_eviction_pass():
    guard = VRAMBudgetGuard(min_free_gb=1.0)
    loader = MagicMock()
    loader._loaded_model = None
    loader.base_url = "http://localhost:11434"
    loader._pool = KeepAlivePool(max_size=2)

    # Set eviction order with phi-4-mini-ud:latest (2.8GB)
    with (
        patch("cognition.morpheus.monitor.get_gpu_memory_info") as mock_vram,
        patch("ollama.Client") as mock_client,
    ):
        # Initial free: 1.5GB. Required: 3.0GB. Safety: 1.0GB.
        # We need at least 4.0GB total VRAM, so we need to free 2.5GB.
        # Evicting phi-4-mini-ud:latest (2.8GB) will increase free to 4.3GB.
        # 4.3GB - 3.0GB = 1.3GB >= 1.0GB -> should return True!
        mock_vram.return_value = {"free_gb": 1.5}

        assert guard.guard_vram(3.0, loader) is True


@pytest.mark.asyncio
async def test_vram_budget_guard_all_essential():
    # Finding 5: all models are essential, eviction cannot free enough VRAM -> should return False
    guard = VRAMBudgetGuard(min_free_gb=1.0)
    loader = MagicMock()
    loader._loaded_model = "phi-4-mini-ud:latest"  # loaded
    loader._pool = KeepAlivePool(max_size=2)
    loader._pool.add("smollm3-3b:latest")

    with patch("cognition.morpheus.monitor.get_gpu_memory_info") as mock_vram:
        # Free is 0.5GB. Required: 5.0GB. Since all models in EVICTION_ORDER are either loaded, core, or in pool,
        # eviction cannot free enough space.
        mock_vram.return_value = {"free_gb": 0.5}
        assert guard.guard_vram(5.0, loader) is False


@pytest.mark.asyncio
async def test_predict_next_models():
    scheduler = MorpheusScheduler()
    # Transition history: draft -> critique -> draft
    scheduler._usage_history["draft"] = [time.time()]
    scheduler._last_role = "draft"

    # Record transitions
    scheduler._session_patterns["draft->critique"] = 3
    scheduler._session_patterns["draft->vision"] = 1

    predictions = scheduler._predict_next_models()
    # Most likely transition from draft is critique
    assert predictions[0] == "critique"


@pytest.mark.asyncio
async def test_pool_full_and_core_model_loaded():
    # Finding 5: pool full, tinyllama loaded -> tinyllama stays in pool, LRU non-core is evicted
    loader = ModelLoader(base_url="http://localhost:11434")
    loader._sync_from_ollama_unlocked = MagicMock()
    loader._pool.add("model_a")
    time.sleep(0.01)
    loader._pool.add("model_b")

    # Now load tinyllama:latest (core model)
    with (
        patch("ollama.Client") as mock_client,
        patch("cognition.morpheus.monitor.get_gpu_memory_info") as mock_vram,
    ):
        mock_vram.return_value = {"free_gb": 5.0}
        mock_client.return_value.chat.return_value = {"message": "ok"}

        # Load tinyllama:latest
        res = loader.load("tinyllama:latest")
        assert res is True
        # Pool size is still max 2 (excluding core models or total max_size = 2)
        # Since tinyllama:latest is in CORE_MODELS, active pool size is the non-core ones.
        # Since active_pool_size was 2 (model_a and model_b), load("tinyllama:latest") should keep model_b (newer) and tinyllama, while model_a is evicted!
        assert loader._pool.contains("tinyllama:latest")
        assert loader._pool.contains("model_b")
        assert not loader._pool.contains("model_a")


@pytest.mark.asyncio
async def test_predict_preload_insufficient_vram():
    # Finding 5: predicted model has insufficient VRAM -> should skip preload
    scheduler = MorpheusScheduler()
    scheduler._usage_history["draft"] = [time.time()]
    scheduler._last_role = "draft"
    scheduler._session_patterns["draft->critique"] = 2

    with (
        patch("src.utils.service_locator.get_bootstrap_loader") as mock_get_loader,
        patch("cognition.morpheus.scheduler.get_gpu_memory_info") as mock_vram,
    ):
        mock_loader = MagicMock()
        mock_loader.loaded = "draft"
        mock_get_loader.return_value = mock_loader

        # Free is 1.5GB, critique (phi-4-mini-ud:latest) requires 2.8GB.
        # 1.5GB - 2.8GB = -1.3GB < 1.0GB (safety budget) -> should skip preload!
        mock_vram.return_value = {"free_gb": 1.5}

        scheduler._preload_model_in_background("phi-4-mini-ud:latest")
        # Loader load should NOT be called!
        mock_loader.load.assert_not_called()
