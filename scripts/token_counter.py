import os
import sys
import tiktoken

def count_tokens(file_path, encoding_name="cl100k_base"):
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return 0
    
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(content))
    return num_tokens

def main():
    files = [
        "AGENTS.md",
        "GEMINI.md",
        ".cursorrules"
    ]
    
    total = 0
    print("-" * 40)
    print(f"{'File':<20} | {'Tokens':<10}")
    print("-" * 40)
    
    for file in files:
        count = count_tokens(file)
        print(f"{file:<20} | {count:<10}")
        total += count
    
    print("-" * 40)
    print(f"{'TOTAL':<20} | {total:<10}")
    print("-" * 40)
    
    # Recommendation based on 2048/4096 thresholds
    if total > 2048:
        print(f"STATUS: Context Cache Recommended (Total > 2048)")
    else:
        print(f"STATUS: Under 2048 Threshold (Caching efficiency lower)")

if __name__ == "__main__":
    main()
