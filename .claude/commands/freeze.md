# /freeze - Restrict Edits to a Directory

Lock all file edits to a specific directory for this session. Any Edit or Write operation targeting a file outside the boundary will be **blocked** (not just warned).

## Setup

$ARGUMENTS

Ask the user which directory to restrict edits to:

- If `$ARGUMENTS` is provided, use that path directly as the freeze boundary.
- Otherwise, ask: "Which directory should I restrict edits to? Files outside this path will be blocked."

Once confirmed, write the absolute path to `D:\Hank\.claude\freeze-dir.txt`:

```powershell
Set-Content -Path "D:\Hank\.claude\freeze-dir.txt" -Value "<ABSOLUTE_PATH>" -NoNewline
```

Then confirm: "Freeze boundary set to `<path>`. All edits outside this directory are now blocked by the `check-freeze.ps1` hook."

## To remove freeze

```powershell
Remove-Item "D:\Hank\.claude\freeze-dir.txt" -ErrorAction SilentlyContinue
```

Or use `/unfreeze`.
