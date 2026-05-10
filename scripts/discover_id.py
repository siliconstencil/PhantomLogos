import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

ids = [
    'models/gemini-1.5-flash', 
    'gemini-1.5-flash', 
    'models/gemini-2.0-flash', 
    'gemini-2.0-flash', 
    'models/gemini-3.1-flash-live-preview',
    'gemini-3.1-flash-live-preview',
    'gemini-3-flash',
    'models/gemini-3-flash'
]

print("--- Model Discovery ---")
for i in ids:
    try:
        res = client.models.generate_content(model=i, contents='ping')
        print(f"PASS: {i}")
    except Exception as e:
        print(f"FAIL: {i} ({e})")
