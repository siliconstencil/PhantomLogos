# Security Risk Matrix: Phantom Logos Workspace
**Generated:** 2026-05-11 [18:00 PT]
**Type:** READ-ONLY Static Analysis
**Scope:** <PROJECT_ROOT> (all .py, .js, config, and log files)

---

## 1. google.generativeai Deprecation Impact

### Severity: LOW
The migration from the deprecated `google.generativeai` package to the new `google.genai` SDK is **complete**.

### Findings

| File | Line | Reference | Verdict |
|------|------|-----------|---------|
| `<PROJECT_ROOT>/tests\test_phase_11_9_integrity.py` | 60 | `import google.generativeai` | **BENIGN** -- This is a test that verifies the old package is NOT installed (wraps in try/except ImportError and calls `pytest.fail()` if found). |
| `<PROJECT_ROOT>/src\architrave\gateway_client.py` | 7-8 | `from google import genai` / `from google.genai import types` | Clean migration |
| `<PROJECT_ROOT>/scripts\verify_models.py` | 2 | `from google import genai` | Clean |
| `<PROJECT_ROOT>/scripts\sovereign_audit.py` | 2 | `from google import genai` | Clean |
| `<PROJECT_ROOT>/scripts\list_models.py` | 2 | `from google import genai` | Clean |
| `<PROJECT_ROOT>/scripts\genai_manager.py` | 4 | `from google import genai` | Clean |
| `<PROJECT_ROOT>/scripts\discover_id.py` | 2 | `from google import genai` | Clean |
| `<PROJECT_ROOT>/scripts\audit_capabilities.py` | 2 | `from google import genai` | Clean |
| `<PROJECT_ROOT>/tests\test_gemini_context_cache.py` | 3 | `from google import genai` | Clean |

### Recommendation
None required. The single remaining reference is a deprecation-detection test -- it is correct and should stay.

---

## 2. Path Traversal / Command Injection Audit

### Severity: MEDIUM

### 2.1 subprocess.run / Popen usage in Python

| File | Line | Code Snippet | Risk |
|------|------|-------------|------|
| `<PROJECT_ROOT>/cognition\morpheus\sweeper.py` | 129 | `subprocess.run(["taskkill", "/F", "/IM", "ollama*", "/T"], capture_output=True)` | **LOW** -- Hardcoded args, no user input |
| `<PROJECT_ROOT>/cognition\morpheus\sweeper.py` | 133 | `subprocess.Popen(["cmd", "/c", "start", "ollama", "app"], shell=True)` | **MEDIUM** -- `shell=True` is a code smell. Args are hardcoded (no injection vector), but spawns a cmd.exe subshell unnecessarily. |
| `<PROJECT_ROOT>/cognition\morpheus\sweeper.py` | 231 | `subprocess.run(["git", "-C", snapshot_path, "gc", "--prune=now", "--quiet"], check=True)` | **LOW** -- `snapshot_path` is derived from `opencode_home` (env). If env is poisoned, this could inject. Mitigated by `check=True`. |
| `<PROJECT_ROOT>/cognition\morpheus\monitor.py` | 33 | `subprocess.run(["nvidia-smi", "--query-gpu=...", ...], creationflags=...)` | **LOW** -- Hardcoded args |
| `<PROJECT_ROOT>/src\muscle\local_runtime.py` | 106 | `subprocess.Popen(cmd, ...)` where `cmd` contains `model_rel_path`, `mmproj_rel_path` | **MEDIUM** -- Model paths constructed from config/registry values. If registry is tampered, arbitrary binary execution is possible. |
| `<PROJECT_ROOT>/src\muscle\local_runtime.py` | 130 | `subprocess.run(["taskkill", "/F", "/IM", "llama*", "/T"], ...)` | **LOW** -- Hardcoded args |
| `<PROJECT_ROOT>/src\muscle\local_runtime.py` | 132 | `subprocess.run(["pkill", "-f", "llama"], ...)` (unreachable on win32) | **LOW** |
| `<PROJECT_ROOT>/src\muscle\reranker.py` | 83 | `subprocess.run([binary, "-m", self.model_path, "--temp", "0.0", "-p", payload], ...)` | **MEDIUM** -- `binary` is a config-driven path. `payload` is JSON from user query. If binary is swapped or payload contains malformed control chars, risk exists. |
| `<PROJECT_ROOT>/src\utils\sandbox.py` | 79 | `subprocess.run([sys.executable, script_path], capture_output=True, ...)` | **LOW** -- Calls same Python interp with a temp file. Environment is stripped to a safe minimal set. Forbidden path patterns are regex-blocked. |
| `<PROJECT_ROOT>/tests\test_hermes_bridge.py` | 14 | `subprocess.run(full_cmd, ...)` where `full_cmd = [sys.executable, cli_path] + cmd_args` | **LOW** -- Test context; `cmd_args` comes from test inputs, not external user data. |
| `<PROJECT_ROOT>/_tmp_outdated.py` | 3 | `subprocess.run([sys.executable, "-m", "pip", "list", ...])` | **LOW** -- Orphaned scratch file, hardcoded args. |
| `<PROJECT_ROOT>/src\lachesis\verifiers\evaluator.py` | 30 | `(r"os\.system", "unsafe os.system call")` -- regex pattern in flaw list | **INFORMATIONAL** -- This detects unsafe patterns in code being evaluated, not usage within the evaluator itself. |

### 2.2 Subprocess usage in JavaScript

| File | Line | Code | Risk |
|------|------|------|------|
| `<PROJECT_ROOT>/.opencode\plugins\websearch.js` | 14 | `Bun.spawn(["python", scriptPath, args.query], { env: { ...process.env } })` | **LOW** -- `args.query` is user-controlled but only passed as a positional arg to a Python script. No shell=True. Environment is inherited (whole `process.env`), which is slightly broad. |

### 2.3 Key Risks Summary
1. **`shell=True` in `sweeper.py:133`** -- Unnecessary subshell. Should use `subprocess.Popen(["ollama", "app"])` without cmd.exe wrapper.
2. **`local_runtime.py:106`** -- Constructs command from config paths that could be tampered (model path injection).
3. **`reranker.py:83`** -- `binary` path from config could be swapped; `payload` is JSON but served to a C++ binary.

### Recommendations
- Remove `shell=True` in sweeper.py:133 -- use direct Popen with `ollama` executable path.
- Audit `local_runtime.py` to validate `model_rel_path` against an allowlist before executing.
- Add path validation for `reranker.py` binary path.

---

## 3. Hardcoded Secrets Scan (scratch/)

### Severity: LOW

All seemingly "secret" values in `<PROJECT_ROOT>/scratch\` are either:
- **(a)** Placeholder strings like `api_key="not-needed"` for QWED local inference
- **(b)** Environment variable names like `os.getenv("ANTIGRAVITY_GATEWAY_URL")` -- not the actual value
- **(c)** Token/context usage logs like `"tokens_used"` which are telemetry, not secrets

### Detailed Matches

| File | Line | Content | Verdict |
|------|------|---------|---------|
| `scratch/sympy_verifier_monolith_backup.py` | 57 | `api_key="not-needed"` | **BENIGN** -- Placeholder for local-only QWED API |
| `scratch/sympy_verifier_monolith_backup.py` | 65 | `api_key="not-needed"` | **BENIGN** -- Same pattern |
| `scratch/test_gateway_inference.py` | 12 | `os.environ["ANTIGRAVITY_GATEWAY_URL"] = "http://localhost:32553"` | **BENIGN** -- Localhost address, not a credential |
| `scratch/test_gateway_inference.py` | 14 | `os.environ["PYDANTIC_AI_GATEWAY_API_KEY"] = "antigravity-native"` | **BENIGN** -- Hardcoded dummy key for local routing |
| `scratch/reasoning_nodes_bck_5.6.26.py` | 144-149 | Reads `GEMINI_API_KEY` / `GOOGLE_API_KEY` from env, validates, then injects into GoogleModel constructor | **INFORMATIONAL** -- Backup of old code; reads from env, not hardcoded |
| `scratch/final_sovereign_verify.py` | 16 | `gateway_url = os.getenv("ANTIGRAVITY_GATEWAY_URL", ...)` | **BENIGN** -- Reads from env |

### Recommendation
No actual secrets found hardcoded in scratch/. The `"antigravity-native"` and `"not-needed"` values are designed dummy credentials for local-routing.

---

## 4. Integrity Violation History

### Severity: HIGH (Systemic Issue)

### 4.1 Primary Log (`logs/system/watchdog/integrity_violations.log`)
**Total violations recorded:** 59
**Date range:** 2026-05-09 to 2026-05-11
**All violations resulted in: Rollback executed.**

### Timeline of Notable Events

| Timestamp | Affected File | Detail |
|-----------|---------------|--------|
| 2026-05-09 21:39:51 | `cognition/sophia/sophia.py` | 11,084 -> 9,705 bytes (12.4% drop) |
| 2026-05-09 21:54:45 | `src/architrave/model_registry.py` | 6,678 -> 5,035 bytes (24.6% drop) |
| 2026-05-09 21:55:36 | `src/lachesis/codebase_mapper.py` | 11,260 -> 1,477 bytes (86.9% drop) |
| 2026-05-10 15:23:10 | `scratch/integrity_test.txt` | File deletion detected |
| 2026-05-10 23:14:40 | `.vscode/settings.json` | Size drop (second occurrence) |
| 2026-05-10 23:17:34 | `.antigravity/walkthroughs/main_walkthrough.md` | Size drop |
| 2026-05-11 00:41:18 | `pyproject.toml` | Size drop |
| **2026-05-11 01:23:03** | **34 files (bulk event)** | **All scripts/ files truncated** -- This is a MASSIVE bulk integrity failure affecting every script in the repo. |
| 2026-05-11 01:36:12 | `agent/skills/error-self-recovery/SKILL.md` | Size drop |
| 2026-05-11 01:36:12 | `agent/skills/telemetry/SKILL.md` | Size drop |
| 2026-05-11 01:43:42 | `agent/skills/telemetry/SKILL.md` | Size drop (second time) |
| 2026-05-11 14:04:38 | `.antigravity/walkthroughs/main_walkthrough.md` | Size drop |

### 4.2 Secondary Log (`logs/integrity_violations.log`)
**Total violations recorded:** 6
**Date range:** 2026-05-08
**Affected files:** `agent/hermes.yaml` (4x), `src/lachesis/file_watchdog.py` (3x)
**Notable:** `hermes.yaml` dropped from 437 -> 34 bytes (92.2% loss) twice in the same second.

### Pattern Analysis
1. **Bulk event at 01:23:03** -- 34 files truncated in the same second. This is the most critical event. Likely caused by a faulty bulk write operation (possibly `replace_file_content` or auto-formatter).
2. **Recurring target files:** `.vscode/settings.json` (2x), `telemetry/SKILL.md` (2x), `hermes.yaml` (4x), `file_watchdog.py` (3x) -- these files appear to be frequent truncation targets.
3. **Scripts/ directory total wipe (01:23:03):** Every file in <PROJECT_ROOT>/scripts/ was hit simultaneously. This represents a systemic write failure.

### 4.3 Watchdog Logs
- `logs/system/watchdog/watchdog_v2.log` exists but is a **binary file** (cannot be read as text).
- This suggests the watchdog daemon may be writing unstructured/binary log data instead of plaintext.

### Recommendations
1. **IMMEDIATE:** Investigate the 01:23:03 bulk event on 2026-05-11. Determine the root cause (agent truncation, disk error, or intentional).
2. **HIGH:** Audit the `file_changelog.py` or any agent path that bulk-writes to `scripts/`.
3. **MEDIUM:** Convert `watchdog_v2.log` to plaintext (CSV or JSON Lines) for proper forensic analysis.
4. **MONITOR:** Files `.vscode/settings.json`, `hermes.yaml`, and `file_watchdog.py` appear to be recurring truncation targets -- add them to a high-priority watchlist.

---

## 5. File Permission / Access Audit

### Severity: MEDIUM

### 5.1 Env Files Found

| File Path | Status |
|-----------|--------|
| `<PROJECT_ROOT>/.env` | **EXISTS** -- Contains environment variables. Blocked from direct read by EnvSitter policy (correctly so). |
| `.opencode\.gitignore` | Exists (separate) |
| `projects\autoresearch\.gitignore` | Exists (separate) |

### 5.2 Gitignore Protection
- `.gitignore` contains `.env*` -- the `.env` file **is** properly gitignored.
- However: `.env*` also matches `.envrc`, `.env.local`, etc., which is acceptable.

### 5.3 Credential Files
- **No `credentials.json`** found anywhere in the workspace.
- **No `.keyring/` directory** present on disk (gitignored anyway).
- **No `secrets.yaml`** or similar found.

### 5.4 Secret Management Architecture
The system uses a **layered secret strategy** (implemented in `src/utils/security_utils.py`):
1. **Primary:** Windows Credential Manager via `keyring` library (`PhantomLogos` service).
2. **Fallback:** `.env` file (plaintext).
3. **Validation:** All keys matching `AIza*` pattern are validated via regex (`validate_cloud_key`).

### 5.5 Scripts with Direct Env Reads (Potential Issue)
These scripts bypass `security_utils.py` and read API keys directly:

| File | Reads | Issue |
|------|-------|-------|
| `scripts/verify_models.py` | `os.getenv(''GEMINI_API_KEY'')` | INFO -- Legacy direct read |
| `scripts/list_models.py` | `os.getenv(''GEMINI_API_KEY'')` | INFO |
| `scripts/discover_id.py` | `os.getenv(''GEMINI_API_KEY'')` | INFO |
| `scripts/audit_capabilities.py` | `os.getenv(''GEMINI_API_KEY'')` | INFO |
| `scripts/genai_manager.py` | `os.environ.get("GOOGLE_API_KEY", "api")` | LOW -- Fallback default `"api"` is suspicious (not a real key, but could cause auth errors) |
| `src/architrave/gateway_client.py` | `os.getenv("ANTIGRAVITY_GATEWAY_URL", ...)` | OK -- Uses the layered security path through the Sovereign Gateway |

### Recommendations
1. **MEDIUM:** Consider migrating all 5 `scripts/*.py` files to use `security_utils.load_secrets_to_env()` instead of direct `os.getenv()`.
2. **LOW:** Investigate whether `.env` can be encrypted (e.g., `sops`, `git-crypt`) or moved to Windows Data Protection API (DPAPI).
3. **LOW:** `.env*` in `.gitignore` is correct -- verify with periodic audit.

---

## 6. Vulnerable Dependency Scan

### Severity: LOW

### 6.1 Dependency Versions (from `requirements.txt`)

| Dependency | Pinned Version | Notes |
|------------|---------------|-------|
| `requests` | 2.33.1 | Current -- Above vulnerability threshold (vulns patched in 2.31+) |
| `httpx` | 0.28.1 | Current -- No known critical CVEs in this range |
| `urllib3` | (transitive) | Inherited from `requests`/`httpx` |
| `cryptography` | (transitive) | Not directly pinned |
| `google-genai` | >=1.74.0 (pyproject.toml) | New SDK -- no known vulns |

### 6.2 Deprecated Crypto Usage (MD5)

| File | Line | Usage | Risk |
|------|------|-------|------|
| `<PROJECT_ROOT>/cognition\mnemosyne\file_changelog.py` | 76 | `hashlib.md5(f.read()).hexdigest()` | **LOW** -- Used for change detection (compare file versions), not for security/cryptography. Collision resistance is irrelevant for this use case. |
| `<PROJECT_ROOT>/src\lachesis\mapper\ast_parser.py` | 74 | `hashlib.md5(content.encode("utf-8")).hexdigest()[:16]` | **LOW** -- Used for content deduplication in AST parsing cache. Truncated to 16 hex chars (64 bits). Not security-critical. |

Note: `snapshot_manager.py` correctly uses `hashlib.sha256()` for integrity snapshots.

### 6.3 Other Security-Relevant Patterns

| Pattern | Found? | Files |
|---------|--------|-------|
| `eval()` | NO | None |
| `exec()` | NO | None |
| `pickle` | NO | None |
| `shelve` | NO | None |
| `marshal` | NO | None |
| `os.system` | NO (used as detection pattern only) | Only found as a regex pattern in evaluator.py:30 |
| SQL injection | NO | All queries use parameterized `?` placeholders |

### Recommendations
1. **LOW:** Replace MD5 with SHA-256 in `file_changelog.py` and `ast_parser.py` for defense-in-depth, even though not strictly needed for their use case.
2. **LOW:** Run `pip-audit` or `safety check` periodically against `requirements.txt`.

---

## 7. Additional Findings

### 7.1 Environment Variable Leakage in Subprocess
- `websearch.js:15` passes `{ ...process.env }` to `Bun.spawn`. The entire host environment (including API keys) is inherited by the subprocess. This is a **LOW** concern for local-only execution but would be elevated if the plugin were distributed.

### 7.2 Orphaned File: `_tmp_outdated.py`
- A standalone script `<PROJECT_ROOT>/_tmp_outdated.py` executes `pip list --outdated` via subprocess. This appears to be a temporary artifact and should be removed from the workspace root.

---

## Risk Matrix Summary

| # | Finding | Severity | Impact | Likelihood | Priority |
|---|---------|----------|--------|------------|----------|
| 4.1 | 59 integrity violations (bulk truncation events) | **HIGH** | Data loss / file corruption | Confirmed recurring | **P0-CRITICAL** |
| 2.1 | `shell=True` in sweeper.py | **MEDIUM** | Unnecessary subshell escalation | Low (hardcoded args) | P2 |
| 2.1 | Model path injection in local_runtime.py | **MEDIUM** | Arbitrary binary execution | Low (needs config tamper) | P2 |
| 2.1 | Binary path in reranker.py unvalidated | **MEDIUM** | Arbitrary binary execution | Low (needs config tamper) | P2 |
| 5.1 | `.env` plaintext secrets on disk | **MEDIUM** | Credential disclosure | Low (file is gitignored) | P2 |
| 5.5 | 5 scripts bypass security_utils.py | **LOW** | Inconsistent secret loading | Medium (but scripts are low-use) | P3 |
| 6.2 | MD5 used in 2 files | **LOW** | No cryptographic security impact | Low (non-security use) | P3 |
| 1 | google.generativeai in test only | **LOW** | None (deprecation test) | None | P4-INFO |
| 3 | No hardcoded secrets in scratch/ | **NONE** | N/A | N/A | CLEARED |
| 6.1 | All dependency versions current | **NONE** | N/A | N/A | CLEARED |
| 6.3 | No eval/exec/pickle/shelve found | **NONE** | N/A | N/A | CLEARED |
| 7.1 | process.env leakage in websearch.js | **LOW** | Environment vars inherited by subprocess | Low (local-only) | P4-INFO |
| 4.3 | watchdog_v2.log is binary | **LOW** | Forensics impaired | Confirmed | P3 |
| 7.2 | `_tmp_outdated.py` orphaned file | **LOW** | Workspace clutter | Confirmed | P4-INFO |

---

## Immediate Action Items (P0-CRITICAL)

### 1. Investigate the 2026-05-11 01:23:03 Bulk Truncation
- **59 total violations**, with **34 files hit simultaneously** at 01:23:03.
- All `scripts/` directory files were truncated in the same second.
- Determine whether this was:
  - An agentic write error (faulty `replace_file_content` call)
  - A Disk I/O or filesystem issue (unlikely given selective targeting)
  - An auto-formatter (e.g., `ruff`, `black`) that ran on the wrong target
- **Action:** Run `git log --oneline --since="2026-05-10" --until="2026-05-12" -- scripts/` and `git diff HEAD@{2026-05-11} scripts/` to check git history.

### 2. Recurring Truncation Targets
- `file_watchdog.py` truncated 3 times on 2026-05-08
- `hermes.yaml` truncated 4 times on 2026-05-08
- `.vscode/settings.json` truncated twice on 2026-05-10
- `telemetry/SKILL.md` truncated twice on 2026-05-11
- **Action:** Add these files to a priority watchlist in `snapshot_manager.py`. Manually restore from git if rollback failed silently.

### 3. Verify Current File Sizes
- Run `for f in scripts/*.py; do Write-Output "$f : $(Get-Item $f).Length"; done` to check if any files are still truncated (rollback may have failed for some).

---

*End of Report*
