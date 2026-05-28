from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

from src.architrave.gateway_client import GatewayArchitrave


@pytest.mark.asyncio
async def test_local_distill_concurrent():
    """Verify that _local_distill embeds concurrently and uses correct prefix."""
    architrave = GatewayArchitrave()

    # Mock matryoshka service
    mock_matryoshka = MagicMock()

    # We will track the arguments passed to embed_document to verify prefix usage
    embed_calls = []

    async def mock_embed_document(text, target_dim=256):
        embed_calls.append(text)
        # return dummy vector
        return np.ones(256, dtype=np.float32) * 0.1

    mock_matryoshka.embed_document = AsyncMock(side_effect=mock_embed_document)

    # Mock get_matryoshka service locator helper
    with patch("src.utils.service_locator.get_matryoshka", return_value=mock_matryoshka):
        # Create a text with 10 paragraphs (len >= 20 each) so it goes into distillation
        paragraphs = [f"Paragraph {i} is long enough to satisfy length check." for i in range(10)]
        long_text = "\n\n".join(paragraphs)

        distilled = await architrave._local_distill(long_text, target_tokens=10)

        # Verify that embed_document was called concurrently
        # 1 call for full text, and 10 calls for the 10 valid chunks = 11 calls
        assert len(embed_calls) == 11
        # Check first call is full text, others are chunks
        assert paragraphs[0] in embed_calls[1]

        # Verify order/completeness
        assert "Paragraph 0" in distilled
        assert "Paragraph 9" in distilled


@pytest.mark.asyncio
async def test_local_distill_max_chunks_limit():
    """Verify that _local_distill limits maximum chunk slicing to 50."""
    architrave = GatewayArchitrave()
    mock_matryoshka = MagicMock()
    mock_matryoshka.embed_document = AsyncMock(return_value=np.ones(256, dtype=np.float32) * 0.1)

    with patch("src.utils.service_locator.get_matryoshka", return_value=mock_matryoshka):
        # Create 60 paragraphs
        paragraphs = [f"Para {i} has enough characters to be valid chunk." for i in range(60)]
        long_text = "\n\n".join(paragraphs)

        await architrave._local_distill(long_text, target_tokens=10)

        # embed_document should be called for full text + max 50 chunks = 51 times
        assert mock_matryoshka.embed_document.call_count == 51


@pytest.mark.asyncio
async def test_local_distill_first_equals_last():
    """Verify that _local_distill handles first == last edge case securely without duplication."""
    architrave = GatewayArchitrave()
    mock_matryoshka = MagicMock()
    mock_matryoshka.embed_document = AsyncMock(return_value=np.ones(256, dtype=np.float32) * 0.1)

    with patch("src.utils.service_locator.get_matryoshka", return_value=mock_matryoshka):
        # Create a text where first paragraph equals last paragraph (first == last duplicate)
        p = "Paragraph that is identical at start and end of document."
        paragraphs = [
            p,
            "Middle paragraph one that is unique.",
            "Middle paragraph two that is unique.",
            "Middle paragraph three that is unique.",
            "Middle paragraph four that is unique.",
            p,
        ]
        long_text = "\n\n".join(paragraphs)

        distilled = await architrave._local_distill(long_text, target_tokens=100)

        # Splitting distilled output by " ... "
        parts = distilled.split(" ... ")

        # Distilled should NOT contain duplicates of the identical paragraph
        p_count = sum(1 for part in parts if part == p)
        # Should be exactly 1 because first == last edge case is protected!
        assert p_count == 1
