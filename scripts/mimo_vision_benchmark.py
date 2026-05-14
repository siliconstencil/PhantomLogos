import asyncio
import json
import os
import subprocess
import sys
import time

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils.ollama_utils import get_ollama_client


async def get_vram_usage():
    try:
        output = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,nounits,noheader"],
            encoding="utf-8",
        )
        return float(output.strip()) / 1024.0  # Convert MB to GB
    except:
        return 0.0


async def benchmark_mimo(image_path: str):
    print("=== MiMo-VL Vision Benchmark (Axis 14) ===")
    print(f"Image: {image_path}")

    model_name = "mimo-vl:repaired"
    client = get_ollama_client()

    # 1. Warm-up / Load check
    print(f"Loading model: {model_name}...")
    start_load = time.monotonic()
    # We trigger a dummy request to ensure it's loaded
    await client.generate(model=model_name, prompt="hi", stream=False)
    load_time = time.monotonic() - start_load
    print(f"Model Load/Warm-up: {load_time:.2f}s")

    vram_start = await get_vram_usage()
    print(f"Baseline VRAM: {vram_start:.2f} GB")

    # 2. Performance Test
    prompt = (
        "Describe the text on the microchip and the holographic diagrams around it. Be precise."
    )
    print(f"Prompt: {prompt}")

    with open(image_path, "rb") as f:
        image_bytes = f.read()

    print("\n--- Starting Inference ---")
    start_inf = time.monotonic()

    # We use stream=True to measure TTFT (Time to First Token)
    ttft = 0
    full_response = ""
    async for chunk in await client.generate(
        model=model_name, prompt=prompt, images=[image_bytes], stream=True
    ):
        if ttft == 0:
            ttft = time.monotonic() - start_inf
            print(f"TTFT (Time to First Token): {ttft:.2f}s")
        full_response += chunk.get("response", "")

    end_inf = time.monotonic()
    total_latency = end_inf - start_inf
    vram_peak = await get_vram_usage()

    print("\n--- Metrics ---")
    print(f"Total Inference Time: {total_latency:.2f}s")
    print(f"Peak VRAM Usage: {vram_peak:.2f} GB")
    print(f"VRAM Delta: {vram_peak - vram_start:.2f} GB")

    print("\n--- MiMo-VL Analysis ---")
    print(full_response)

    # Save results to data/
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "model": model_name,
        "metrics": {
            "load_time_sec": load_time,
            "ttft_sec": ttft,
            "latency_sec": total_latency,
            "vram_peak_gb": vram_peak,
            "vram_delta_gb": vram_peak - vram_start,
        },
        "analysis": full_response,
    }

    report_path = "data/mimo_benchmark_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=4)
    print(f"\nReport saved to: {report_path}")


if __name__ == "__main__":
    img_path = sys.argv[1] if len(sys.argv) > 1 else "mimo_vision_test_bench.png"
    asyncio.run(benchmark_mimo(img_path))
