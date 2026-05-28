# Copyright (c) 2026 Sovereign OS
# Dynamic patch script for superlocalmemory site-packages server.py

from pathlib import Path


def main():
    venv_path = Path("D:/Hank/.venv")
    server_path = venv_path / "Lib/site-packages/superlocalmemory/mcp/server.py"

    if not server_path.exists():
        print(f"[ERROR] server.py not found at: {server_path}")
        return

    content = server_path.read_text(encoding="utf-8")

    # 1. Inject "rerank" into _ESSENTIAL_TOOLS
    if "rerank" not in content:
        # Locate _ESSENTIAL_TOOLS registration block
        target_essential = "_ESSENTIAL_TOOLS: set[str] = {"
        if target_essential in content:
            content = content.replace(target_essential, target_essential + '\n    "rerank",')
            print("[INFO] Injected 'rerank' into _ESSENTIAL_TOOLS.")
        else:
            print("[ERROR] Could not find _ESSENTIAL_TOOLS declaration.")
            return
    else:
        print("[INFO] 'rerank' already exists in server.py, checking tool definition.")

    # 2. Inject rerank tool definition before the main block
    rerank_tool_def = """
@_target.tool()
def rerank(query: str, documents: list[str], top_n: int = 3) -> dict:
    \"\"\"Rerank a list of documents based on semantic similarity to a query.

    Args:
        query: The search query to rank documents against.
        documents: A list of document texts to rank.
        top_n: Number of top results to return.
    \"\"\"
    import numpy as np
    from superlocalmemory.core.engine_wiring import init_embedder

    if not documents:
        return {"results": []}

    engine = get_engine()
    embedder = getattr(engine, "embedder", None)
    if embedder is None:
        try:
            embedder = init_embedder(engine._config)
        except Exception:
            pass

    if embedder is None:
        return {"results": [{"index": i, "score": 1.0, "text": doc} for i, doc in enumerate(documents[:top_n])]}

    try:
        q_vec_raw = embedder.embed(query)
        if q_vec_raw is None:
            return {"results": []}
        q_vec = np.array(q_vec_raw)

        doc_vecs_raw = embedder.embed_batch(documents)
        scored = []
        for i, d_vec_raw in enumerate(doc_vecs_raw):
            if d_vec_raw is None:
                continue
            d_vec = np.array(d_vec_raw)
            score = np.dot(q_vec, d_vec) / (np.linalg.norm(q_vec) * np.linalg.norm(d_vec))
            scored.append({"index": i, "score": float(score), "text": documents[i]})

        scored.sort(key=lambda x: x["score"], reverse=True)
        return {"results": scored[:top_n]}
    except Exception as e:
        logger.warning(f"MCP rerank tool failed: {e}")
        return {"results": []}
"""

    if "def rerank(query: str" not in content:
        main_block = 'if __name__ == "__main__":'
        if main_block in content:
            content = content.replace(main_block, rerank_tool_def + "\n\n" + main_block)
            print("[INFO] Injected rerank tool definition into server.py.")
        else:
            print("[ERROR] Could not find __main__ block.")
            return
    else:
        print("[INFO] rerank tool definition already exists in server.py.")

    server_path.write_text(content, encoding="utf-8")
    print("[SUCCESS] Dynamic patching of site-packages server.py completed successfully.")


if __name__ == "__main__":
    main()
