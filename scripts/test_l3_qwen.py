import asyncio
import os
import sys
from typing import List

# Setup path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.utils.ollama_utils import get_ollama_client

async def test_l3_audit(dir_path: str):
    print(f"L3 Audit Test starting for: {dir_path}")
    
    # Load files
    files = ["models.py", "logic.py", "app.py", "schemas.py"]
    context = ""
    for f in files:
        fpath = os.path.join(dir_path, f)
        if os.path.exists(fpath):
            with open(fpath, encoding="utf-8") as file:
                context += f"FILE: {f}\n```python\n{file.read()}\n```\n\n"
    
    # Use Qwen 3.5 4B as L3 Auditor for better VRAM hygiene (2.9 GB)
    model = "qwen3.5-4b-ud:latest"
    print(f"Using Model: {model}")
    
    prompt = f"""You are the L3 Auditor (Lachesis). 
Your task is to audit the following code for dependency integrity.
Check if all imports in 'app.py' and 'logic.py' are valid and if the imported names actually exist in the referenced files (models.py, schemas.py).

CONTEXT:
{context}

Return a detailed audit report. If there is a broken import, highlight it clearly.
"""

    response = await get_ollama_client().chat(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    
    print("\n=== L3 AUDIT REPORT ===")
    print(response['message']['content'])

if __name__ == "__main__":
    asyncio.run(test_l3_audit("tests/sandbox_test"))
