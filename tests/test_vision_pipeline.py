import os
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest
from PIL import Image

from cognition.mnemosyne.visual_store import VisualStore
from cognition.sophia.gnosis.axis_14_visual import _build_axis_14
from src.clotho.krisis import should_use_tier
from src.utils.image_optimizer import optimize_image_for_vlm


# [SRC:axis_14]
@pytest.fixture(scope="module")
def test_image():
    test_dir = "scratch/test_vision"
    os.makedirs(test_dir, exist_ok=True)
    img_path = os.path.join(test_dir, "sample.png")
    img = Image.new("RGB", (100, 100), color="red")
    img.save(img_path)
    yield img_path


def test_image_optimizer(test_image):
    """Verify format and cache logic."""
    opt_path = optimize_image_for_vlm(test_image)
    assert opt_path.endswith(".jpg")
    assert "vision_cache" in opt_path
    assert os.path.exists(opt_path)


def test_krisis_tier_enforcement():
    """Verify Tier 3 enforcement for visual tasks."""
    state = {"task": "Analyze this screenshot", "ru_flow_tier": 2}
    tier = should_use_tier(state)
    assert tier == "expert"

    state_no_vision = {"task": "Write a python script", "ru_flow_tier": 2}
    tier_no = should_use_tier(state_no_vision)
    assert tier_no == "standard"


def test_gnosis_axis_14_injection():
    """Verify Axis 14 context injection."""
    with patch("cognition.sophia.gnosis.axis_14_visual.get_visual") as mock_visual_getter:
        mock_store = MagicMock()
        mock_store.get_recent.return_value = [
            {
                "variant": "ocr",
                "timestamp": "2026-05-08",
                "description": "Detected text: 'Hello World'",
            }
        ]
        mock_visual_getter.return_value = mock_store

        context = _build_axis_14("test_session")
        assert "AXIS 14" in context
        assert "Hello World" in context


@pytest.mark.asyncio
async def test_visual_store_integration(test_image):
    """Verify VisualStore and SemanticStore integration."""
    store = VisualStore()
    session_id = "integration_test_session"

    with patch.object(store, "_get_text_embedding", new_callable=AsyncMock) as mock_embed:
        mock_embed.return_value = np.zeros(256)
        store.semantic_store.add_memories = MagicMock()

        await store.store_vision(
            image_path=test_image,
            description="Integrated test description",
            variant="creative",
            session_id=session_id,
        )

        recent = store.get_recent(session_id, limit=1)
        assert len(recent) == 1
        assert recent[0]["variant"] == "creative"
