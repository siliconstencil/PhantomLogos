"""
One-time migration script to move secrets from .env to Windows Credential Manager.
Run: python scripts/migrate_keys.py
"""
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from dotenv import load_dotenv
    from src.utils.security_utils import set_secret, validate_gemini_key
    import keyring
except ImportError as e:
    print(f"Error: Missing dependencies ({e}). Run 'pip install keyring python-dotenv'")
    sys.exit(1)

def migrate():
    load_dotenv()
    keys = ["GEMINI_API_KEY", "GOOGLE_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY"]
    
    migrated_count = 0
    for key in keys:
        val = os.getenv(key)
        if val:
            if key in ("GEMINI_API_KEY", "GOOGLE_API_KEY") and not validate_gemini_key(val):
                print(f"[-] Skipping {key}: Invalid format.")
                continue
            
            print(f"[*] Migrating {key} to Windows Credential Manager...")
            if set_secret(key, val):
                print(f"[+] Successfully migrated {key}.")
                migrated_count += 1
            else:
                print(f"[!] Failed to migrate {key}.")
        else:
            print(f"[-] {key} not found in .env.")

    if migrated_count > 0:
        print(f"\n[SUCCESS] Migrated {migrated_count} keys.")
        print("[IMPORTANT] You can now safely remove these keys from your .env file.")
        print("[IMPORTANT] Ensure .env is added to .gitignore.")
    else:
        print("\nNo keys were migrated.")

if __name__ == "__main__":
    migrate()
