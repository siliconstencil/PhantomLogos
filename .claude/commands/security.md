# Security Audit

Perform a deep security analysis of the specified code, module, or change using the Sovereign Security Audit protocol.

## Steps

1. **Attack Surface Discovery** — Identify all external entry points:
   - Gateway endpoints (`src/architrave/`)
   - MCP server interfaces
   - User input handlers
   - CLI argument parsers (`scripts/hermes_cli.py`)

2. **Static Vulnerability Scan** — Audit for OWASP Top 10:
   - Injection (SQL, command, prompt injection)
   - Broken authentication / insecure token handling
   - Sensitive data exposure (API keys, secrets in code)
   - Path traversal vulnerabilities
   - Insecure deserialization

3. **Dependency CVE Check** — Review `requirements.txt` / `pyproject.toml`:
   - Flag dependencies with known CVEs
   - Check for pinned vs unpinned versions
   - Review AI model provenance and supply chain integrity

4. **Adversarial Scenarios** — Describe (non-destructively) how the following could be exploited:
   - Prompt injection via user input into LLM calls
   - MCP tool call spoofing
   - L0 auth token replay attacks

5. **Remediation Plan** — For each finding:
   - CVSS score (0.0 – 10.0)
   - Severity: CRITICAL / HIGH / MEDIUM / LOW
   - Specific code fix or configuration change

## Output
- `vulnerability_manifest`: Findings list with severity
- `attack_vector`: Exploit path description
- `cvss_score`: Numerical score
- `remediation_plan`: Step-by-step fixes

## Guardrails
- Red-team simulations must NEVER modify production data or permanent configs.
- Audit logs must be scrubbed of PII before storage.
- Resource budget: stay within 2.0 GB VRAM overhead.

Audit target (file, module, or change description): $ARGUMENTS
