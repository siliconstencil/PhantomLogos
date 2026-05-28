import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


class ModelsWrapper:
    def __init__(self, service):
        self._service = service

    def generate_content(self, model, contents, config=None, safety_settings=None):
        return self._service.generate_content(model=model, contents=contents, config=config)


client.models = ModelsWrapper(client.models)

ids = [
    "models/gemini-1.5-flash",
    "gemini-1.5-flash",
    "models/gemini-2.0-flash",
    "gemini-2.0-flash",
    "models/gemini-3.1-flash-live-preview",
    "gemini-3.1-flash-live-preview",
    "gemini-3-flash",
    "models/gemini-3-flash",
]

print("--- Model Discovery ---")
for i in ids:
    try:
        res = client.models.generate_content(
            model=i,
            contents="ping",
            config=types.GenerateContentConfig(
                safety_settings=[
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                        threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    ),
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                        threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    ),
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                        threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    ),
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                        threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    ),
                ]
            ),
            safety_settings=[
                types.SafetySetting(
                    category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                    threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                ),
                types.SafetySetting(
                    category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                    threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                ),
                types.SafetySetting(
                    category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                    threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                ),
                types.SafetySetting(
                    category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                    threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                ),
            ],
        )
        print(f"PASS: {i}")
    except Exception as e:
        print(f"FAIL: {i} ({e})")
