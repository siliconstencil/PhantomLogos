# VRAM Stability and Model Switching Test Plan

This document was prepared to test the Phantom Logos system's 7.0 GB GPU VRAM limit protection, the Morpheus daemon memory cleanup mechanism and stability during model switches. [2:45 PM PT]

## 1. Required Hardware and Environment
- An NVIDIA GPU with at least 6 GB of VRAM.
- The Morpheus daemon must be active (python src/clotho/bootstrap.py --daemon).
- GPU_TOTAL_VRAM_GB=7.0 must be set in the .env file.

## 2. Test Scenarios

### Scenario A: Morpheus Daemon Startup and Health Check
- **Steps:**
  1. Run the `python src/clotho/bootstrap.py --daemon` command.
  2. Inspect the `logs/system/morpheus/morpheus.log` file to verify that the daemon started successfully.
- **Expected Result:** The log file must contain "Morpheus Daemon started successfully" and the PID.

### Scenario B: VRAM Cleanup on Model Switch (Morpheus.flush)
- **Steps:**
  1. Run the `scripts/baseline_benchmark.py` script.
  2. Watch the Morpheus daemon logs during a model switch (for example when switching from the L2 to the L3 model).
- **Expected Result:** The logs must show that Morpheus triggered the `Morpheus.flush()` method, that the old model was cleared from VRAM and that space was freed for the new model. Total VRAM usage must not exceed 7.0 GB at any stage.
