import asyncio
import os
import sys

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils.ollama_utils import get_ollama_client


async def main():
    client = get_ollama_client()
    try:
        print("Testing MiMo-VL (Text-only mode)...")
        res = await client.generate(
            model="mimo-vl:repaired", prompt="Who are you? Respond in one sentence.", stream=False
        )
        print(f"Response: {res.get('response')}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
