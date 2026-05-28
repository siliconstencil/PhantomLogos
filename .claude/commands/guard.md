# /guard - Full Sovereign Guard Mode

Activates both `/careful` (destructive command interception) and `/freeze` (directory boundary enforcement) simultaneously.

## Activation

$ARGUMENTS

1. Run `/careful` — confirm safety hook is active.
2. Run `/freeze $ARGUMENTS` — set the freeze boundary directory.
   - If no directory argument provided, ask the user: "Which directory should edits be restricted to?"

Both protections are now active:
- Destructive commands → `permissionDecision: ask` (prompt before execution)
- Edits outside freeze dir → `permissionDecision: deny` (hard block)

## Status check

```powershell
$f = "D:\Hank\.claude\freeze-dir.txt"
if (Test-Path $f) { "Freeze: $(Get-Content $f)" } else { "Freeze: OFF" }
```

## Deactivate

Use `/unfreeze` to remove the directory boundary. Careful mode is always-on via project hook.
