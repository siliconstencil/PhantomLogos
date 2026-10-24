# Phantom Logos Developer Contribution Guide (CONTRIBUTING.md)

Thank you for wanting to contribute to the Phantom Logos autonomous operating system project. This document describes our development standards, rules and contribution processes.

---

## 1. Git Branch Strategy

To keep the development process stable, git branches are managed according to the following standards:

* **master**: The production and stable release branch. Pushing directly to this branch is forbidden (except for L0-authorized emergency patches).
* **feature/<feature-name>**: New features, improvements or refactoring work are developed on these branches, and once their tests are complete a Pull Request (PR) is opened against the master branch.
* **hotfix/<bug-name>**: Created for critical bugs on the master branch that must be fixed urgently.

---

## 2. BA-01 Language and Emoji Governance Protocol

When contributing to the project, the **BA-01** rules must be followed strictly:

1. **Operator Interaction (Chat & Interface)**: The agents talk to the operator (L0) in the operator's language, set in `.antigravity/rules.json` (Turkish by default). Repository documentation is in **English**.
2. **Core Codebase (Code, Logs, DB, Config)**: Python code, comments, variable names, database schemas and log records must be entirely in **English (ASCII-only)**. Using Turkish characters (ç, ğ, ı, ö, ş, ü, etc.) in code or comments is forbidden.
3. **EMOJI_BAN (Emoji Ban)**: Using emojis or decorative special characters anywhere in the codebase, logs, commit messages and documents is **strictly forbidden**.

---

## 3. Pre-commit and Code Quality Standards

Before committing your changes, it is recommended to run the code quality tools. The project uses **Ruff** for formatting and static analysis:

```bash
# Code formatting
ruff format src/ cognition/ scripts/ tests/

# Static analysis and rule checks (Linting)
ruff check src/ cognition/ scripts/ tests/ --fix
```

You can also verify static type checking with `pyright`:
```bash
pyright src/
```

---

## 4. L0_AUTH_TOKEN Protocol

Security and autonomous integrity protection (Watchdog/Guardian) is active in the system. Before performing actions that write files, delete files or change configuration in the codebase, an L0 approval token must be created:

```bash
python scripts/create_l0_token.py
```
This command opens an authorization window valid for 60 seconds at `data/snapshots/L0_AUTH_TOKEN`. Unauthorized or expired write operations will be automatically reverted by the Guardian (Rollback).

---

## 5. Standards for Adding Tests

You should add the relevant tests for every new feature or bug fix you write. Tests must be placed in the `tests/` directory and labeled according to the following categories:

* **smoke**: Fast tests that verify basic build and stability.
* **integration**: Tests that require a real Ollama service, databases or MCP server connections.
* **slow**: Heavy integration tests that take longer than 30 seconds to run.

Test marker labeling example:
```python
import pytest

@pytest.mark.smoke
def test_my_feature():
    assert True
```

---

## 6. Pull Request (PR) Process

1. Create a branch containing your changes.
2. Make sure the Ruff, Pyright and pytest checks pass locally.
3. Push your branch to the remote and open a Pull Request against the master branch.
4. In the PR description, include a summary of the changes, which tests verified them, and the BA-01 compliance confirmation.
