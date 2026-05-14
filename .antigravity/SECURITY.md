# Phantom Logos: Security & Secret Management (SECURITY.md)

Phantom Logos implements a **Zero-Trust Secret Architecture** to ensure that sensitive credentials (API keys, DB passwords) are never exposed in logs or version control.

---

## 1. Secret Storage Hierarchy

1.  **Primary: Windows Credential Manager (Keyring)**
    - Secrets are stored in the OS-level secure vault.
    - Accessed via the `keyring` Python library.
    - **Service Name:** `PhantomLogos`

2.  **Secondary: Environment Variables (.env)**
    - Read-only fallback for environments where Keyring is unavailable (CI/CD, Fresh Install).
    - `.env` files are strictly gitignored.

---

## 2. Security Utilities (`src/utils/security_utils.py`)

- `load_secrets_to_env()`: This function attempts to pull keys from Keyring first. If not found, it falls back to the `.env` file and populates `os.environ`.
- `validate_gemini_key(key)`: Regex-based validation to ensure API keys start with `AIza` and follow Google's format.

---

## 3. Command Security

- **Shell Removal:** The `shell` tool has been removed from the `ToolBridge` to prevent command injection.
- **Path Traversal Guard:** The `ls` tool uses `os.path.commonpath` to ensure agents cannot view files outside of the project root.
- **SQL Injection Sanitization:** Manual alphanumeric filtering for session IDs and SQLAlchemy ORM parameter binding for all database interactions (Axis 1-14).

---
## 4. Reporting Vulnerabilities
If you identify a logic flaw or a security loophole, please record it in the **Verification Axis (Axis 11)** and notify the Sovereign (L0) immediately.

---
*Last Hardened: 2026-05-10*
