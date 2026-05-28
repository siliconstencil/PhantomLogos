---
name: background-agent
description: Managing persistent background daemons, scheduled tasks, and long-running
  maintenance processes.
version: 1.0.0
license: MIT
compatibility: opencode
model_role: light
allowed_tools:
- ls
- vram
- report
- mcp_slm_remember
tier: 1
---
# Background Agent

Manages daemonized background processes that run independently of agent task loops.

## Active Daemons

### Morpheus Sweeper
- VRAM fragmentation cleanup and heal_ollama.
- Gateway health check (circuit breaker status).
- Weekly/monthly summary generation.
- Scheduled via `scheduler.py` with 30-second tick interval.

### Sovereign Shield Watchdogs
- `snapshot_manager.py`: 30-second periodic SHA-256 snapshots.
- `file_watchdog.py`: 30-second mtime-based integrity polling.

### Scheduler
- Load/unload model scheduling.
- Periodic health checks.
- Retention and pruning policies.

## Best Practices
- Daemons should be CPU-light; pin to E-cores via `psutil`.
- Always check `ActivityMonitor.is_busy()` before spawning new daemons.
- Log all daemon activity to OperationalStore (Axis 7).
