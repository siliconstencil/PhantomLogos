import json
import os
import subprocess
import sys
import time

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def get_vram_gb() -> float:
    try:
        output = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            encoding="utf-8",
        )
        return round(float(output.strip()) / 1024, 2)
    except Exception:
        return 0.0


print(f"Initial VRAM: {get_vram_gb()} GB")

try:
    print("Attempting to import GLiNER2 from gliner2...")
    from gliner2 import GLiNER2

    # Monkey-patch to prevent UnicodeEncodeError on Windows (Brain emoji in _print_config)
    GLiNER2._print_config = lambda self, config: None

    start_time = time.time()
    print("Loading model 'fastino/gliner2-base-v1' using GLiNER2...")
    model = GLiNER2.from_pretrained("fastino/gliner2-base-v1")

    end_time = time.time()
    print(f"Model loaded successfully in {end_time - start_time:.2f}s")
    print(f"Post-load VRAM: {get_vram_gb()} GB")

    text = "Bill Gates founded Microsoft in 1975."
    # GLiNER2 API uses a schema
    schema = (
        model.create_schema()
        .entities(["person", "organization", "date"])
        .relations(["founded", "uses"])
    )

    results = model.extract(text, schema=schema)
    print(f"Test result: {json.dumps(results, indent=2)}")

except Exception as e:
    import traceback

    traceback.print_exc()
    print(f"ERROR: {e}")
    sys.exit(1)
