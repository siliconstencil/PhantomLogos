import asyncio
import os
import sys

# Add src to path
sys.path.append(os.getcwd())


async def test_math_async():
    from src.lachesis.verifiers.llm_engine import LLMMathEngine

    engine = LLMMathEngine()

    print("[TEST] Testing LLMMathEngine.verify_math_llm (async)...")
    # Simple problem to check async flow
    problem = "What is 2+2?"
    result = await engine.verify_math_llm(problem, light=True)

    print(f"[RESULT] is_valid: {result.get('is_valid')}")
    print(f"[RESULT] content: {result.get('result')}")

    if result.get("is_valid") is not None:
        print("[SUCCESS] Async math verification flow works.")
    else:
        print("[FAILURE] Async math verification failed.")


if __name__ == "__main__":
    asyncio.run(test_math_async())
