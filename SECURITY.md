# Phantom Logos: Security Policy

---

## Reporting Vulnerabilities

If you discover a security vulnerability, please report it responsibly:

**GitHub Private Advisory (preferred):**
https://github.com/siliconstencil/PhantomLogos/security/advisories/new

**Email:**
admin@siliconstencil.com

Please include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

We aim to respond within 72 hours and will coordinate a fix before public disclosure.

---

## Security Architecture

### Secret Storage Hierarchy

1. **Primary: Windows Credential Manager (Keyring)**
   - Secrets stored in OS-level secure vault via `keyring` Python library
   - Service name: `PhantomLogos`

2. **Secondary: Environment Variables (.env)**
   - Read-only fallback for CI/CD and fresh installs
   - `.env` files are strictly gitignored - never committed

### Security Utilities (`src/utils/security_utils.py`)

- `load_secrets_to_env()`: Pulls keys from Keyring first, falls back to `.env`
- Path traversal guard: `ls` tool uses `os.path.commonpath` to prevent directory escape
- SQL injection protection: SQLAlchemy ORM parameter binding for all DB interactions

### Command Security

- Shell tool removed from ToolBridge to prevent command injection
- All agent tool calls go through formal dispatch map (whitelist-only)

---

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.1.x   | Yes       |
| < 1.0   | No        |

---

*Last Updated: 2026-05-30*
