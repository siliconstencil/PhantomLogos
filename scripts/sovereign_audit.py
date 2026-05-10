import os
from google import genai
from src.utils.logging_config import setup_logger

logger = setup_logger("sovereign_audit")

# NO API KEYS - Pure Sovereign ADC
os.environ.pop("GOOGLE_API_KEY", None)
os.environ.pop("GEMINI_API_KEY", None)

print("--- Antigravity Sovereign Audit (2026 GDC Path) ---")
try:
    client = genai.Client(
        vertexai=True,
        project="projects/830662377830",
        location="us-central1"
    )
    print("Models accessible via Native ADC:")
    for m in client.models.list():
        print(f"- {m.name}")
except Exception as e:
    print(f"Sovereign Access Failed: {e}")
