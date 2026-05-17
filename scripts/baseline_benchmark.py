import asyncio
import json
import os
import subprocess
import sys
import time
import uuid
from datetime import datetime

import numpy as np
from sqlalchemy import text

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Antigravity Imports
from cognition.mnemosyne.episodic_store import EpisodicStore
from cognition.mnemosyne.operational_store import OperationalStore
from cognition.mnemosyne.semantic_store import SemanticStore
from src.architrave.gateway_client import GatewayArchitrave
from src.clotho.bridge.base import ToolBridge
from src.clotho.control_handoff import clotho_handoff
from src.utils.ollama_utils import get_ollama_client

# Constants
SCRATCH_DIR = "D:\\Hank\\scratch"
DATA_DIR = "D:\\Hank\\data"
TEST_IMAGE_PATH = "D:\\Hank\\scratch\\test.png"
BASELINE_VERSION = "1.0.0"


class BaselineBenchmark:
    def __init__(self, simulate_gateway_down: bool = False):
        self.simulate_gateway_down = simulate_gateway_down
        self.gateway = GatewayArchitrave()
        if simulate_gateway_down:
            print("SIMULATION: Gateway down mode active.")
            self.gateway.trigger_circuit_breaker(3600)

        self.ollama = get_ollama_client()
        self.semantic_store = SemanticStore()
        self.episodic_store = EpisodicStore()
        self.op_store = OperationalStore()
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "baseline_version": BASELINE_VERSION,
            "system_info": {},
            "steps": [],
            "summary": {},
        }
        os.makedirs(SCRATCH_DIR, exist_ok=True)
        os.makedirs(DATA_DIR, exist_ok=True)

    def _get_vram_gb(self) -> float:
        try:
            output = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                encoding="utf-8",
            )
            return round(float(output.strip()) / 1024, 2)
        except Exception:
            return 0.0

    async def _get_ollama_list(self) -> str:
        try:
            process = await asyncio.create_subprocess_exec(
                "ollama", "list", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await process.communicate()
            return stdout.decode()
        except Exception:
            return "Ollama not found or error"

    async def gather_system_info(self):
        print("Gathering system info...")
        self.results["system_info"] = {
            "ollama_version": "Unknown",
            "gpu": "Unknown",
            "python_version": sys.version,
            "gateway_reachable": await self.gateway.is_gateway_healthy(),
            "ollama_list": await self._get_ollama_list(),
        }
        try:
            gpu_output = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=gpu_name", "--format=csv,noheader"], encoding="utf-8"
            )
            self.results["system_info"]["gpu"] = gpu_output.strip()
        except Exception:
            pass

    def create_test_image(self):
        print(f"Creating test image at {TEST_IMAGE_PATH}...")
        try:
            from PIL import Image

            img = Image.new("RGB", (100, 100), color=(73, 109, 137))
            img.save(TEST_IMAGE_PATH)
        except ImportError:
            with open(TEST_IMAGE_PATH, "wb") as f:
                f.write(
                    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfe\x05\xfe\x1a\x06\x06\x00\x00\x00\x00IEND\xaeB`\x82"
                )

    async def _measure_ttft(self, model: str, prompt: str) -> int | None:
        """Measures Time To First Token for Ollama calls."""
        try:
            start = time.monotonic()
            async for chunk in await self.ollama.chat(
                model=model, messages=[{"role": "user", "content": prompt}], stream=True
            ):
                ttft = int((time.monotonic() - start) * 1000)
                return ttft
        except Exception:
            return None

    async def measure_step(self, name: str, coro, prompt: str = ""):
        print(f"Executing step: {name}...")
        session_id = f"baseline_{uuid.uuid4().hex[:8]}"
        vram_start = self._get_vram_gb()
        start_time = time.monotonic()

        status = True
        error = None
        warnings = []
        ttft = None
        model_used = "Unknown"
        fallback_chain = []
        input_tokens = 0
        output_tokens = 0

        # Inject session_id if it's a coroutine that supports it
        # (This is a simplified approach, we'll manually handle Sophia loops)

        try:
            if "Sophia Loop" in name:
                # Use clotho_handoff with the generated session_id
                result = await asyncio.wait_for(
                    clotho_handoff(prompt, session_id=session_id), timeout=150
                )

                # Metadata Retrieval from Axis 1 & 7
                with self.episodic_store.engine.connect() as conn:
                    # Query latest episode for this session
                    query = text(
                        "SELECT action, detail, tokens_used, outcome FROM episodes WHERE session_id = :sid ORDER BY id DESC"
                    )
                    rows = conn.execute(query, {"sid": session_id}).fetchall()
                    if rows:
                        model_used = "Clotho/Sophia"
                        # v1.0.0 Limitation: tokens_used might be 0 as analyzed
                        output_tokens = sum(r[2] or 0 for r in rows)
                        if output_tokens == 0:
                            warnings.append(
                                "v1.0.0 Baseline: Token logging missing/zero in EpisodicStore"
                            )

                        for r in rows:
                            if r[1] and "semantic_relations" in r[1] and "0 rows" in r[1]:
                                warnings.append("K0.1 BUG: 0 row semantic_relations detected")

            elif name == "Vision Call":
                ttft = await self._measure_ttft("mimo-7b-vl-ud:latest", prompt)
                result = await asyncio.wait_for(coro, timeout=120)
                model_used = "mimo-7b-vl-ud:latest"

            elif name == "Embedding Call":
                ttft = await self._measure_ttft("nomic-embed-text-v2-moe-q8:latest", prompt)
                result = await asyncio.wait_for(coro, timeout=60)
                model_used = "nomic-embed-text-v2-moe-q8:latest"
                output_tokens = 256

            else:
                result = await coro
                if "Semantic Search" in name:
                    model_used = "LanceDB/Hybrid"

        except Exception as e:
            status = False
            error = str(e)
            print(f"Step {name} failed: {e}")

        latency_ms = int((time.monotonic() - start_time) * 1000)
        vram_end = self._get_vram_gb()

        step_data = {
            "name": name,
            "prompt_truncated": (prompt[:50] + "...") if prompt else None,
            "model_used": model_used,
            "tier": 2 if "Sophia" in name else 0,
            "fallback_chain": fallback_chain,
            "latency_ms": latency_ms,
            "ttft_ms": ttft,
            "vram_gb": vram_start,
            "vram_peak_gb": max(vram_start, vram_end),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "success": status,
            "warnings": warnings,
            "error": error,
        }
        self.results["steps"].append(step_data)

    async def run_benchmark(self):
        await self.gather_system_info()
        self.create_test_image()

        # Step 1-3: Sophia Loops
        prompts = [
            "Design a modular authentication system for a FastAPI app.",
            "Write a Python script for 14-axis memory management in a multi-agent system.",
            "Implement a Python context manager for SQLite WAL checkpointing with automatic rollback on integrity errors",
        ]
        for i, p in enumerate(prompts, 1):
            await self.measure_step(f"Sophia Loop {i}", None, prompt=p)

        # Step 4-5: Semantic Search
        queries = ["system integrity rules", "VRAM optimization techniques"]
        for i, q in enumerate(queries, 1):
            dummy_vec = np.random.rand(256)
            await self.measure_step(
                f"Semantic Search {i}",
                asyncio.to_thread(
                    self.semantic_store.search, dummy_vec, "baseline_session", query_text=q
                ),
                prompt=q,
            )

        # Step 6-7: Tool Calls
        bridge = ToolBridge("baseline_session")
        await self.measure_step("Tool Call (ls)", bridge.execute("ls", "."), prompt=".")
        await self.measure_step("Tool Call (vram)", bridge.execute("vram", {}))

        # Step 8: Vision Call
        vision_prompt = "Describe the contents of this image."

        async def vision_call():
            client = get_ollama_client()
            return await client.chat(
                model="mimo-7b-vl-ud:latest",
                messages=[{"role": "user", "content": vision_prompt, "images": [TEST_IMAGE_PATH]}],
            )

        await self.measure_step("Vision Call", vision_call(), prompt=vision_prompt)

        # Step 9: Embedding Call
        embed_text = "Mnemosyne is the personification of memory in Greek mythology. In the Antigravity system, it represents the 14-axis memory architecture."

        async def embed_call():
            client = get_ollama_client()
            return await client.embeddings(
                model="nomic-embed-text-v2-moe-q8:latest", prompt=embed_text
            )

        await self.measure_step("Embedding Call", embed_call(), prompt=embed_text)

        # Cleanup
        if os.path.exists(TEST_IMAGE_PATH):
            os.remove(TEST_IMAGE_PATH)

        self.generate_summary()
        self.save_results()
        self.compare_with_previous()

    def generate_summary(self):
        steps = self.results["steps"]
        successful = [s for s in steps if s["success"]]
        total_latency = sum(s["latency_ms"] for s in steps)
        total_tokens = sum(s["input_tokens"] + s["output_tokens"] for s in steps)

        self.results["summary"] = {
            "total_latency_ms": total_latency,
            "avg_latency_ms": total_latency // len(steps) if steps else 0,
            "total_tokens": total_tokens,
            "overall_success_rate": len(successful) / len(steps) if steps else 0,
            "peak_vram_gb": max((s["vram_peak_gb"] for s in steps), default=0.0),
            "avg_vram_gb": round(sum(s["vram_gb"] for s in steps) / len(steps), 2)
            if steps
            else 0.0,
        }

    def save_results(self):
        filename = f"baseline_{datetime.now().strftime('%Y%m%d')}.json"
        filepath = os.path.join(DATA_DIR, filename)
        latest_path = os.path.join(DATA_DIR, "baseline_latest.json")

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        with open(latest_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        print(f"\nResults saved to {filepath} and baseline_latest.json")

    def compare_with_previous(self):
        # Placeholder for simple diff logic
        print("\n--- Baseline Comparison Summary ---")
        print("Current version 1.0.0 established.")
        print(f"Peak VRAM: {self.results['summary']['peak_vram_gb']} GB")
        print(f"Total Latency: {self.results['summary']['total_latency_ms']} ms")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--simulate-gateway-down", action="store_true")
    args = parser.parse_args()

    benchmark = BaselineBenchmark(simulate_gateway_down=args.simulate_gateway_down)
    asyncio.run(benchmark.run_benchmark())
