# Cross-Platform Compatibility Test Plan

This document was prepared to verify that the Phantom Logos system runs without issues on Unix-like operating systems other than Windows (macOS, Linux, etc.), and to verify virtual environment integrity and the dynamic path resolution mechanisms. [2:45 PM PT]

## 1. Virtual Environment and Dependency Check
- All dependencies in `pyproject.toml` must be platform-independent.
- It must be tested that the `keyring>=25.0.0` package installs correctly into the virtual environment and can be imported.

## 2. Test Scenarios

### Scenario A: Smart MCP Configurator (setup_mcp_config.py)
- **Steps:**
  1. Run the `setup_mcp_config.py` script.
  2. Open the generated `mcp_config.json` file and verify that:
     - on Windows, backslash (`\\`) and `.venv\\Scripts\\python.exe` paths are used,
     - on macOS/Linux, forward slash (`/`) and `.venv/bin/python` paths are used.
- **Expected Result:** An error-free, dynamic configuration in the format appropriate for the operating system must be generated.

### Scenario B: Shell Scripts (BAT and SH Equivalence)
- **Steps:**
  1. Verify that on Windows the `.bat` (for example `run_morpheus.bat`) and `.vbs` scripts,
  2. and on macOS/Linux the `.sh` scripts (for example `run_morpheus.sh`), together with executable permissions (`chmod +x run_morpheus.sh`), start without issues.
- **Expected Result:** On both platforms the Morpheus background daemon must start successfully and produce logs.
