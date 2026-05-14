import os
import sys

import tiktoken
from google import genai
from google.genai import types

# --- CONFIG ---
API_KEY = os.environ.get("GOOGLE_API_KEY", "api")
MODEL_NAME = "gemini-3.1-flash-lite-preview"
CACHE_THRESHOLD = 4096  # New lower threshold for Gemini 3.1 series


def count_tokens(file_path, encoding_name="cl100k_base"):
    if not os.path.exists(file_path):
        return 0
    with open(file_path, encoding="utf-8", errors="ignore") as f:
        content = f.read()
    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(content))


def sync_cache(files):
    """Creates a cache using the google-genai SDK."""
    client = genai.Client(api_key=API_KEY)

    # Merge file contents
    full_content = ""
    for f_path in files:
        if os.path.exists(f_path):
            with open(f_path, encoding="utf-8") as f:
                full_content += f"--- FILE: {os.path.basename(f_path)} ---\n"
                full_content += f.read() + "\n\n"

    print(f"[*] Uploading {len(full_content)} chars to GenAI Cache...")

    try:
        # GenAI SDK Cache API
        # Note: TTL is provided in seconds (example 3600 = 1 hour)
        cache = client.caches.create(
            model=MODEL_NAME,
            config=types.CreateCachedContentConfig(
                display_name="antigravity_rules_cache",
                contents=[full_content],
                ttl="3600s",
            ),
        )
        print("[+] Cache Created Successfully!")
        print(f"    Name: {cache.name}")
        return cache
    except Exception as e:
        print(f"[!] GenAI Cache Error: {e}")
        return None


def main():
    # Determine absolute paths (based on D:\Hank)
    base_path = "d:\\Hank"
    files = [
        os.path.join(base_path, "AGENTS.md"),
        os.path.join(base_path, "GEMINI.md"),
        os.path.join(base_path, ".cursorrules"),
    ]

    print("-" * 50)
    print(f"{'GenAI Rule File':<30} | {'Tokens':<10}")
    print("-" * 50)

    total = 0
    for f in files:
        name = os.path.basename(f)
        count = count_tokens(f)
        print(f"{name:<30} | {count:<10}")
        total += count

    print("-" * 50)
    print(f"{'TOTAL SYSTEM TOKENS':<30} | {total:<10}")
    print("-" * 50)

    if len(sys.argv) > 1 and sys.argv[1] == "--sync":
        if total < CACHE_THRESHOLD:
            print(
                f"[!] Warning: Total tokens ({total}) < {CACHE_THRESHOLD}. Caching might not be supported/efficient on Gemini 3.1."
            )
        sync_cache(files)
    else:
        print(f"[TIP] Use '--sync' flag to upload these rules to GenAI Cloud Cache ({MODEL_NAME}).")


if __name__ == "__main__":
    main()
