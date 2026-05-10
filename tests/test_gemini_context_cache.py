import os
import pytest
from google import genai

# [SRC:axis_10]
MODEL_ID = "gemini-2.5-flash"

def get_client():
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None
    return genai.Client(api_key=api_key, http_options={"api_version": "v1alpha"})

@pytest.mark.skipif(not (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")), 
                    reason="no GEMINI_API_KEY or GOOGLE_API_KEY set")
@pytest.mark.skipif(os.getenv("HTTP_PROXY") and "localhost:32553" in os.getenv("HTTP_PROXY"),
                    reason="Cache API v1alpha often fails through Gateway proxy")
@pytest.mark.asyncio
async def test_context_caching():
    """Test the creation and listing of Gemini context caches."""
    client = get_client()
    assert client is not None
    
    system_instruction = "You are Antigravity, a professional AI architect. " * 500

    try:
        cache = client.caches.create(
            model=MODEL_ID,
            config={
                "display_name": "antigravity_core_context",
                "system_instruction": system_instruction,
                "ttl": "3600s",
            },
        )
        assert cache.name is not None
        
        caches = list(client.caches.list())
        found = any(c.name == cache.name for c in caches)
        assert found, "Cache created but not found in list."

    except Exception as e:
        pytest.fail(f"Context Caching failed: {e}")
