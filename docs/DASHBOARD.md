# Phantom Logos Web Operator Dashboard (DASHBOARD.md)

This document contains technical details and the user guide for the premium web-based Operator Console (Dashboard) integrated with Phantom Logos Sovereign OS (v1.2.1).

---

## 1. Overview

The Web Operator Dashboard is a modern, premium, and responsive interface designed to monitor the operational status of the Phantom Logos system architecture (Sovereign Gateway and Local Muscle), the 14-Axis Mnemosyne memory status, and system reliability scores.

### Key Features:
- **Overview:** Real-time reliability levels for Sophia, Clotho, and Lachesis agents, VRAM allocation, and the status of active databases (mnemosyne, reliability, spatial).
- **14-Axis Health Matrix:** Line and integrity status of the 14 memory axes (Episodic, Procedural, Goals, etc.), including warning and broken status indicators.
- **Terminal & Logs:** Real-time (JSON-based) tracking of the `logs/system.json` log file.
- **Operator Console (Actions):** Trigger live health check audits and run the system garbage collector directly from the interface.

---

## 2. Installation and Startup

The dashboard uses the `aiohttp` library within the virtual environment (`.venv`) without requiring any additional external dependencies. To start the dashboard, run the following command:

```bash
python scripts/dashboard.py
```

By default, the system will run on port `8080`. You can access the console by navigating to the following address in your browser:
**URL:** [http://localhost:8080](http://localhost:8080)

To customize the port, you can use the `PORT` environment variable:
```bash
set PORT=9000
python scripts/dashboard.py
```

---

## 3. API Endpoints (REST Endpoints)

The dashboard backend service (`src/dashboard/api_server.py`) exposes the following REST API endpoints:

- **`GET /`**: Serves the HTML Operator Console interface.
- **`GET /api/metrics`**: Returns Sophia/System reliability scores, VRAM allocation status, and a 14-Axis SQLite integrity summary in JSON format.
- **`GET /api/logs`**: Reads the last 150 log entries from the `logs/system.json` file and returns them as a parsed JSON structure.
- **`POST /api/trigger-health`**: Runs the live axis health test (`scripts/health_check_14_axes.py`) in the background and returns its output.

---

## 4. Testing

Dashboard API and web server integration tests are automated under `tests/test_dashboard_api.py`:

```bash
pytest tests/test_dashboard_api.py -v
```
