import io
import json
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from ddgs import DDGS

def search(query: str, max_results: int = 8) -> list[dict]:
    results = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", ""),
                })
    except Exception as e:
        return [{"error": str(e)}]
    return results


def main():
    args = sys.argv[1:]
    query = " ".join(args) if args else sys.stdin.read().strip()
    if not query:
        print(json.dumps({"error": "No query provided", "results": []}))
        sys.exit(1)
    results = search(query)
    out = {"query": query, "results": results, "count": len(results)}
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
