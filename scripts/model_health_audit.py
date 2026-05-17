import os
import sys
import time

import ollama

# Set PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from cognition.mnemosyne.operational_store import OperationalStore
from src.utils.logging_config import setup_logger

logger = setup_logger("model_audit")

# Configuration
TEST_IMAGE = os.path.join(os.getcwd(), "data", "test_vision.png")  # Changed to relative-ish
MODELS_TO_AUDIT = [
    {"name": "qwen3.5-4b-ud:latest", "type": "coding"},
    {"name": "phi-4-mini-ud:latest", "type": "reasoning"},
    {"name": "nomic-embed-text-v2-moe-q8:latest", "type": "light"},
]

PROMPTS = {
    "reasoning": "A heavy iron ball and a feather are dropped from the same height in a vacuum. Which one hits the ground first?",
    "coding": "Write a Python function to calculate Fibonacci.",
    "vision": "Describe this image briefly.",
    "light": "Hello, what is your role?",
}


def audit_model(model_info, store):
    name = model_info["name"]
    m_type = model_info["type"]
    prompt = PROMPTS[m_type]

    logger.info(f"AUDIT: Testing {name} ({m_type})...")
    start_time = time.time()

    try:
        content = ""
        if m_type == "vision":
            if not os.path.exists(TEST_IMAGE):
                return {"status": "FAIL", "error": f"Test image missing at {TEST_IMAGE}"}
            with open(TEST_IMAGE, "rb") as f:
                response = ollama.chat(
                    model=name, messages=[{"role": "user", "content": prompt, "images": [f.read()]}]
                )
            content = response["message"]["content"]
        elif "embed" in name:
            # Embedding models do not support chat()
            response = ollama.embeddings(model=name, prompt=prompt)
            # Response might be a dict or a Pydantic object
            emb = (
                response.get("embedding")
                if isinstance(response, dict)
                else getattr(response, "embedding", None)
            )
            content = f"Vector generated: {len(emb)} dims" if emb else "Empty vector"
        else:
            response = ollama.chat(model=name, messages=[{"role": "user", "content": prompt}])
            content = response["message"]["content"]

        duration = time.time() - start_time

        anomalies = []
        if len(content) < 5:
            anomalies.append("Too short")
        if any(char in content for char in ["\U0001f607", "\U0001f680"]):
            anomalies.append("Emoji detected")

        status = "PASS" if not anomalies else "WARNING"

        # Record to OperationalStore (Axis 7)
        store.record_event(
            name=f"audit.{name}",
            level="INFO" if status == "PASS" else "WARNING",
            message=f"Status: {status} | Latency: {duration:.2f}s | Anomalies: {anomalies}",
        )

        return {
            "status": status,
            "duration": round(duration, 2),
            "anomalies": anomalies,
            "preview": content[:100].replace("\n", " ") + "...",
        }
    except Exception as e:
        store.record_event(name=f"audit.{name}", level="ERROR", message=f"Audit failed: {e}")
        return {"status": "FAIL", "error": str(e)}


def run_suite():
    store = OperationalStore()
    print("=== Phantom Logos Model Health Audit (Axis 7 Integration) ===")

    for model in MODELS_TO_AUDIT:
        res = audit_model(model, store)
        print(f"Result: {res['status']} | {model['name']}")

    print("\n[REPORT] Audit finished. Results persisted to Mnemosyne Axis 7.")


if __name__ == "__main__":
    run_suite()
