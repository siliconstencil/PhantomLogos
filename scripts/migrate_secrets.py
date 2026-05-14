import os

import keyring
from dotenv import load_dotenv

SERVICE_NAME = "PhantomLogos"
load_dotenv()

KEYS_TO_MIGRATE = [
    "GATEWAY_API_KEY",
    "GEMINI_API_KEY",
    "DEEPSEEK_API_KEY",
    "HF_TOKEN",
    "GITHUB_PERSONAL_ACCESS_TOKEN",
]


def migrate():
    print(f"Starting migration to Windows Credential Manager ({SERVICE_NAME})...")
    for key in KEYS_TO_MIGRATE:
        value = os.getenv(key)
        if value and "YOUR_" not in value:
            try:
                keyring.set_password(SERVICE_NAME, key, value)
                print(f"[SUCCESS] Migrated {key}")
            except Exception as e:
                print(f"[ERROR] Failed to migrate {key}: {e}")
        else:
            print(f"[SKIP] {key} not set or has placeholder value.")
    print("Migration complete.")


if __name__ == "__main__":
    migrate()
