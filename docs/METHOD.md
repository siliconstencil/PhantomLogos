# Method: building a local agent system with agents, safely

Phantom Logos was built in the first half of 2026 by Silicon Stencil, with AI
coding agents doing much of the typing and a human approving every change.
This page keeps the working rules that held up, so they can be reused without
reading the whole governance set in `.antigravity/` and `AGENTS.md`.

The project is paused at v1.2.1. These rules describe how it was built; they
are not a claim that every part of it still runs today.

## 1. The human approves, the agent proposes

- One authority (called **L0** in the code) approves every write, config change
  and deletion. Read-only analysis can run without approval.
- Approval is a physical step, not a habit: `scripts/create_l0_token.py` mints a
  token that is valid for 60 seconds, and write operations check for it.
- Before any write the agent names two ways the change could break something
  (`PRE_FLIGHT_AUDIT`). It costs a few lines and catches most bad edits early.
- Deleting a file needs a short justification (what depends on it, what replaces
  it) and a verified backup first (`BACKUP_BEFORE_DELETE`,
  `SOVEREIGN_DELETION_GATE`).

## 2. Guard the dangerous commands mechanically

Rules in a prompt get ignored under pressure; a hook that runs before every
shell command does not. The two guards used here are in
[`method/guards/`](method/guards/):

- `check-careful.ps1` asks for confirmation before `rm -r`, `git push --force`,
  `git reset --hard`, `git checkout .`, `DROP TABLE`, `TRUNCATE`,
  `alembic downgrade`, `Remove-Item -Recurse -Force`, `docker system prune` and
  similar. Recursive deletes of build output (`node_modules`, `dist`,
  `__pycache__`, `.venv`, ...) pass without a prompt.
- `check-freeze.ps1` blocks edits outside the folder named in `freeze-dir.txt`
  (one level above the script), for work that must stay inside one module.

Both read the pending tool call as JSON on stdin and answer with a permission
decision, the pre-tool hook format most agent CLIs accept. They are PowerShell
ports of gstack's `check-careful.sh` and `check-freeze.sh`.

The write tools enforce the approval step in code as well:
`src/clotho/bridge/fs.py` refuses to write when the L0 token is missing or
expired.

## 3. Respect the hardware budget

The target machine was a laptop GPU with 8 GB of VRAM. The rules that made it
stable:

- Plan for 7.0 GB and keep 1.0 GB for the operating system.
- Never load two heavy models (> 3 GB) at once; flush VRAM between them
  (`Morpheus.flush()`).
- Compute GPU layer offload (`-ngl`) from the free VRAM at load time instead of
  hard-coding it.
- Small local models do most of the work (3-4B for routine and coding, a
  verifier model for audits). A cloud model is only called for the few tasks
  that need it, and only after a local draft (`RULE-030`, `RULE-032`).

## 4. Turn every failure into a rule

- Each logic failure or runtime error becomes a stored prevention rule
  (`FAILURES_MEMORY`), and repeated rule violations lower the agent's
  reliability score. At 0.3 or below the loop is sent back to a reflection step;
  below 0.2 the run stops (`src/clotho/krisis.py`).
- Three strikes: if the same fix fails three times with nearly the same code,
  the agent stops and writes a post-mortem instead of trying a fourth time.

## 5. Keep memory outside the model

The 14-axis memory (Mnemosyne, SQLite + LanceDB) was designed so that context
survives across sessions and models: episodic, procedural, goals, temporal,
graph, semantic, operational, meta-cognitive, tone, rational, verification,
efficiency, cross-session patterns and visual. Claims an agent makes about the
project cite the axis they came from (`[SRC:axis_N]`), so a reader can check
where a statement came from.

## 6. Be honest about tests

- Every phase ends with a test and verification step, with evidence (logs, test
  output).
- Tests that are skipped are listed with their reason in
  [`tests/IGNORED_TESTS.md`](../tests/IGNORED_TESTS.md) instead of being hidden.
  CI skips tests that need a live Ollama service or a cloud key.

## What is specific to this project

Some rules in `.antigravity/rules.json` are the author's own working
preferences, not general advice, and can be changed freely: the reply language
(Turkish to the operator, English in code), the short-answer limit, the emoji
ban, the Pacific-time timestamp format and the E-core pinning for an Intel
laptop CPU.
