import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

print("--- Antigravity: Sovereign Model Capability Audit ---")
try:
    for m in client.models.list():
        print(f"\nModel: {m.name}")
        print(f"  - Supported Methods: {m.supported_generation_methods}")
        # Check for specific capabilities in model description or name
        if "thinking" in m.name.lower() or "reasoning" in m.name.lower():
            print(f"  - [CONFIRMED] Reasoning native support detected.")
except Exception as e:
    print(f"Audit failed: {e}")
