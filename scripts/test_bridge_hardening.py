import asyncio
import os
from src.clotho.tool_bridge import ToolBridge

async def test_bridge():
    bridge = ToolBridge("test_session")
    
    print("Testing 'ls' on project root...")
    res = await bridge.execute("ls", ".")
    output = res.get("output", str(res))
    print(f"Result: {str(output)[:50]}... (Total {len(str(output))} chars)")
    
    print("\nTesting 'ls' path traversal (../)...")
    res = await bridge.execute("ls", "..")
    output = res.get("output", str(res))
    print(f"Result: {output}")
    
    print("\nTesting 'shell' tool (should be missing)...")
    res = await bridge.execute("shell", "whoami")
    output = res.get("output", str(res))
    print(f"Result: {output}")

if __name__ == "__main__":
    asyncio.run(test_bridge())
