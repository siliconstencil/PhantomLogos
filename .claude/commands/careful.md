# /careful - Destructive Command Guardrails

Safety mode is now **active**. The project-level hook (`check-careful.ps1`) is always running and will intercept the following patterns before execution:

| Pattern | Risk |
|---------|------|
| `rm -r` / `rm --recursive` | Recursive delete |
| `DROP TABLE` / `DROP DATABASE` | SQL data loss |
| `TRUNCATE` | SQL row deletion |
| `git push --force` / `-f` | Remote history rewrite |
| `git reset --hard` | Uncommitted work loss |
| `git checkout .` / `git restore .` | Working tree discard |
| `kubectl delete` | Production impact |
| `docker rm -f` / `docker system prune` | Container loss |
| `alembic downgrade` | DB migration rollback [SRC:axis_1] |
| `Remove-Item -Recurse -Force` | PowerShell recursive delete |

**Safe exceptions** (no warning): `node_modules`, `.next`, `dist`, `__pycache__`, `.cache`, `build`, `.turbo`, `coverage`, `.venv`, `.pytest_cache`

The hook returns `permissionDecision: ask` — you will be prompted to confirm before proceeding.

To activate permanent guard mode (careful + freeze together), use `/guard`.
