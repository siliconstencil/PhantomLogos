import asyncio
import os
import sys
import time
import uuid

# Set project root and PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ["PYTHONPATH"] = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

from cognition.sophia.eidos import ReasoningState
from cognition.sophia.hephaestus import _get_episodic
from cognition.sophia.sophia import run_draft
from src.architrave.model_registry import LOCAL_REASONING_MODEL
from src.utils.ollama_utils import get_ollama_client


async def test_token_logging():
    print("\n--- [K0.3 Test 1] Token Logging & Model Detection ---")
    session_id = f"test_k03_{uuid.uuid4().hex[:6]}"
    state = ReasoningState(
        task="Explain the 3-strike rule in Sovereign OS operational mandates.",
        session_id=session_id,
        flags={"bypass_memory_gate": True},
    )

    # Trigger Sophia Draft
    print("Running Sophia Draft...")
    output, tools = await run_draft(state, thinking=False)

    # Check Episodic Store
    print("Verifying EpisodicStore...")
    episodic = _get_episodic()

    # We need to query the DB directly
    from sqlalchemy import text

    with episodic.engine.connect() as conn:
        query = text(
            "SELECT tokens_used, latency_ms, detail FROM episodes WHERE session_id = :sid ORDER BY id DESC"
        )
        row = conn.execute(query, {"sid": session_id}).fetchone()

        if row:
            tokens = row[0]
            latency = row[1]
            detail = row[2]
            print(f"Tokens Used: {tokens}")
            print(f"Latency: {latency}ms")
            print(f"Detail: {detail}")

            if tokens > 0 and latency > 0 and "Model: " in detail and "Unknown" not in detail:
                print("SUCCESS: Token Logging & Model Detection verified.")
            else:
                print(f"FAILED: tokens={tokens}, latency={latency}, detail={detail}")
                sys.exit(1)
        else:
            print("ERROR: No episode row found in DB.")
            sys.exit(1)


async def test_cache_audit():
    print("\n--- [K0.3 Test 2] Loop 3 Cache Audit ---")
    client = get_ollama_client()
    prompt = "Design a modular authentication system for a FastAPI app."

    # 1. First call (Uncached or warm)
    print("Inference 1 (Standard)...")
    start = time.monotonic()
    await client.generate(model=LOCAL_REASONING_MODEL, prompt=prompt, stream=False)
    lat1 = (time.monotonic() - start) * 1000
    print(f"Latency 1: {lat1:.2f}ms")

    # 2. Second call (Potential cache)
    print("Inference 2 (Same prompt)...")
    start = time.monotonic()
    await client.generate(model=LOCAL_REASONING_MODEL, prompt=prompt, stream=False)
    lat2 = (time.monotonic() - start) * 1000
    print(f"Latency 2: {lat2:.2f}ms")

    # 3. Third call (Seed randomization)
    print("Inference 3 (Random Seed)...")
    seed = int(time.time())
    start = time.monotonic()
    await client.generate(
        model=LOCAL_REASONING_MODEL, prompt=prompt, stream=False, options={"seed": seed}
    )
    lat3 = (time.monotonic() - start) * 1000
    print(f"Latency 3 (Seed={seed}): {lat3:.2f}ms")

    if lat2 < 500 and lat3 > lat2 * 2:
        print(
            f"RESULT: Cache detected. Standard repeats are fast ({lat2:.1f}ms), but random seed forces re-inference ({lat3:.1f}ms)."
        )
    else:
        print(
            f"RESULT: Cache behavior inconclusive (Fast response might be expected for small prompts). Lat2: {lat2:.1f}ms, Lat3: {lat3:.1f}ms"
        )


async def main():
    try:
        await test_token_logging()
        await test_cache_audit()
    finally:
        # Cleanup client to avoid loop closure issues
        client = get_ollama_client()
        # No explicit close needed for ollama AsyncClient usually, but httpx inside it might hang
        pass


if __name__ == "__main__":
    asyncio.run(main())
