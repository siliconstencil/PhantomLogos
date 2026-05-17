import asyncio
import sys
from pathlib import Path

# Add project root to path
root = Path(__file__).resolve().parent.parent
if str(root) not in sys.path:
    sys.path.append(str(root))

from src.architrave.model_registry import resolve_local_model
from src.utils.logging_config import setup_logger
from src.utils.ollama_utils import get_ollama_client

logger = setup_logger("expert_stability_test")


async def test_nomic():
    print("Testing Nomic (Embedding)...", end=" ", flush=True)
    try:
        client = get_ollama_client()
        model = resolve_local_model("embedding")
        resp = await client.embeddings(model=model, prompt="test")
        raw_dim = len(resp.embedding)
        truncated_vec = resp.embedding[:256]
        if len(truncated_vec) == 256:
            print(f"OK (Raw: {raw_dim} -> Sliced: 256)")
            return True
        print(f"FAIL (Truncation error: {len(truncated_vec)})")
        return False
    except Exception as e:
        print(f"FAIL ({e})")
        return False


def test_sympy():
    print("Testing SymPy (Math)...", end=" ", flush=True)
    try:
        from sympy import expand, symbols

        x, y = symbols("x y")
        expr = expand((x + y) ** 2)
        if str(expr) == "x**2 + 2*x*y + y**2":
            print("OK")
            return True
        print(f"FAIL (Unexpected output: {expr})")
        return False
    except Exception as e:
        print(f"FAIL ({e})")
        return False


def test_z3():
    print("Testing Z3 (Formal Ver)...", end=" ", flush=True)
    try:
        from z3 import Int, Solver, sat

        x = Int("x")
        s = Solver()
        s.add(x > 10, x < 20)
        if s.check() == sat:
            print("OK")
            return True
        print("FAIL (Unsat)")
        return False
    except Exception as e:
        print(f"FAIL ({e})")
        return False


async def test_jina():
    print("Testing Jina (Reranker)...", end=" ", flush=True)
    try:
        from src.muscle.reranker import JinaReranker

        r = JinaReranker()
        docs = ["Python is a language", "The fox jumps", "AI is cool"]
        res = r.rerank("Python", docs, top_n=1)
        if res and "results" in res and len(res["results"]) > 0:
            print(f"OK (Top score: {res['results'][0]['score']:.4f})")
            return True
        print("FAIL (No results)")
        return False
    except Exception as e:
        print(f"FAIL ({e})")
        return False


async def test_qwed():
    print("Testing QWED (Logic Audit)...", end=" ", flush=True)
    try:
        from src.lachesis.verifiers.evaluator import AdversarialEvaluator

        evaluator = AdversarialEvaluator(session_id="audit_test")
        qwed_model = resolve_local_model("verification")
        print(f"OK (Model: {qwed_model})")
        return True
    except Exception as e:
        print(f"FAIL ({e})")
        return False


async def test_functiongemma():
    print("Testing FunctionGemma (Router)...", end=" ", flush=True)
    try:
        client = get_ollama_client()
        models = await client.list()
        found = any(m.model and m.model.startswith("functiongemma") for m in models.models)
        if found:
            print("OK (Loaded in Ollama)")
            return True
        print("FAIL (Not found in Ollama tags)")
        return False
    except Exception as e:
        print(f"FAIL ({e})")
        return False


async def run_all():
    print("=== Expert Stability Audit ===\n")
    results = []
    results.append(await test_nomic())
    results.append(test_sympy())
    results.append(test_z3())
    results.append(await test_jina())
    results.append(await test_qwed())
    results.append(await test_functiongemma())

    print(f"\nFinal Score: {sum(results)}/6 expert components operational.")


if __name__ == "__main__":
    asyncio.run(run_all())
