import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

models_to_test = [
    "gemini-1.5-flash",
    "gemini-1.5-flash-latest",
    "gemini-2.0-flash",
    "gemini-2.0-flash-exp",
    "gemini-3.1-flash-live-preview",
    "gemini-2.5-flash",
    "gemini-2.0-flash-thinking-exp-1219"
]

print("Testing Models for generate_content:")
for m_id in models_to_test:
    try:
        # Try without models/ prefix
        client.models.count_tokens(model=m_id, contents="test")
        print(f"OK: {m_id}")
    except Exception as e:
        print(f"FAIL: {m_id} -> {e}")

print("\nTesting Models WITH models/ prefix:")
for m_id in models_to_test:
    full_id = f"models/{m_id}"
    try:
        client.models.count_tokens(model=full_id, contents="test")
        print(f"OK: {full_id}")
    except Exception as e:
        print(f"FAIL: {full_id} -> {e}")
