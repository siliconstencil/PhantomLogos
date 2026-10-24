# Phantom Logos v1.2.1 Installation Guide (INSTALLATION.md)

This document contains the complete steps for developers and operators who want to install and run the Phantom Logos system from scratch.

---

## 1. System Requirements

For the system to run stably and with good performance, the following minimum hardware and software requirements must be met:

* **Operating System**: Windows 10/11, Ubuntu 22.04 LTS or newer, macOS 14 (Sonoma) or newer.
* **Memory (RAM)**: At least 16 GB DDR4/DDR5 RAM.
* **Graphics Card (VRAM)**: An NVIDIA GPU with at least 7.0 GB of available VRAM (for local inference stability).
* **Python Version**: Python >= 3.12 (minimum requirement).

---

## 2. Installing Ollama

The system uses the **Ollama** engine to run local LLM and embedding models. Download and install the Ollama version for your operating system:

* **Windows**: [Ollama for Windows](https://ollama.com/download/windows)
* **macOS**: [Ollama for macOS](https://ollama.com/download/mac)
* **Linux**: [Ollama for Linux](https://ollama.com/download/linux)

After installation, make sure the Ollama service is running in the background (it should be active in the taskbar or under systemd).

---

## 3. Cloning the Repository and Bootstrap Setup

Clone the project and change into the root directory:

```bash
git clone <repo-url> phantom-logos
cd phantom-logos
```

Then run the **Bootstrap** setup script to configure the virtual environment, dependencies, database schema and models in a single step:

```bash
python scripts/bootstrap.py
```

### Bootstrap Parameters (Optional):
* `--skip-models`: Skips the Ollama model download step (use it if you have already downloaded the models or want to manage them manually).
* `--skip-seeds`: Skips the database pre-seed (seeding) steps.
* `--check-only`: Only verifies the current state and integrity without installing anything.
* `--verbose`: Prints detailed installation logs to the screen.

Example (quick setup, skipping the model download):
```bash
python scripts/bootstrap.py --skip-models
```

---

## 4. Environment Variables (.env) Guide

The bootstrap process automatically copies `.env.example` to `.env`. For the system to run, edit the settings in the `.env` file to match your environment:

```env
# Directory containing the GGUF and Ollama models (absolute or relative path)
LLM_MODEL_DIR=./models

# Ollama service connection settings
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_HOST=localhost:11434

# Maximum amount of VRAM to reserve on the GPU (default: 7.0 GB)
GPU_TOTAL_VRAM_GB=7.0

# Security and agent-to-agent (A2A) communication encryption key (must be at least 32 characters)
A2A_SECRET_KEY=your-super-secret-key-min-32-chars

# L0 administrator authorization token lifetime (default: 60 seconds)
L0_AUTH_TOKEN_TTL=60

# Logging level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO
```

---

## 5. Initial Verification and Test Steps

Run the following commands to verify the installation and the stability of the components:

### 1. 14-Axis Memory State Verification:
```bash
python scripts/health_check_14_axes.py
```
Prints the state and data integrity of all 14 axes to the screen.

### 2. Pytest Smoke Tests:
```bash
pytest tests/ -m smoke -v
```
If the 5 basic smoke tests pass (`PASSED`), the installation has been done completely correctly.

---

## 6. Frequently Asked Questions (FAQ)

### Q: I am getting an "Ollama Port Conflict" error. What should I do?
Another service in the background may be blocking port 11434. You can point the `OLLAMA_BASE_URL` and `OLLAMA_HOST` addresses in the `.env` file to another free port and start the Ollama service on that port.

### Q: My graphics card has 6 GB of VRAM. Will the system run?
Yes, it will. However, set the `GPU_TOTAL_VRAM_GB` value in the `.env` file according to your graphics card (e.g. `5.0`). When memory is insufficient, the system will automatically move some model layers to the CPU (offloading).

### Q: The MCP servers do not start, or I get a permission error.
Confirm that the paths in the `.mcp.json` file in the project root directory are correct. Also, refresh the L0 administrator authorization by running `python scripts/create_l0_token.py`.

---

## 7. Troubleshooting

* **System Logs**: All actions in the system and detailed error records are written to `logs/system.json` (structured logs in JSON format) and `logs/system.log` (plain text format). When an error occurs, check these files first.
* **Emergency Reset**: If a lock-up or inconsistency occurs in the databases or MCP sessions, you can run the emergency reset:
  ```bash
  python scripts/emergency_reset.py
  ```
  This operation will clear temporary lock files and restart the services with safe default values.
