---
name: background-agent
description: Managing persistent background daemons, scheduled tasks, and long-running maintenance processes.
version: 1.0.0
license: MIT
compatibility: opencode
when_to_use:
  - Running Morpheus sweeper daemon for VRAM management.
  - Scheduling periodic maintenance (pruning, health checks).
  - Managing background file integrity monitoring.
  - Coordinating async daemon lifecycle with agent tasks.
depends-on:
  - resource-scheduling
metadata:
  audience: developers
  tier: L2-Runner
  workflow: automation
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
