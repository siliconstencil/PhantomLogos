---
name: security-audit
description: Code security auditing, vulnerability scanning, and AI supply chain integrity checks.
version: 1.0.0
license: MIT
compatibility: opencode
when_to_use:
  - Auditing code for OWASP Top 10 vulnerabilities.
  - Scanning dependencies for known CVEs.
  - Reviewing AI model provenance and supply chain integrity.
  - Validating API key handling and secret management.
depends-on:
  - security-first-guardian
metadata:
  audience: developers
  tier: L3-Auditor
  workflow: security
---
# Skill: Security Audit (Sovereign Edition)

Provides deep security analysis, vulnerability scanning, and autonomous Red-Teaming simulations to harden the Sovereign OS against adversarial attacks.

## Workflow
1.  **Attack Surface Discovery**: Map all external entry points (Gateways, MCP servers, User input) using `codebase-topography-analysis`.
2.  **Vulnerability Scanning**:
    - **Static**: Audit code for OWASP Top 10 using regex and AST patterns.
    - **Dynamic**: Scan active dependencies for known CVEs using `Sovereign Registry` data.
3.  **Red-Team Simulation**:
    - Execute non-destructive payload injections (e.g., prompt injection, path traversal) in a sandboxed environment.
    - Test the `Sovereign Shield` response time and effectiveness.
4.  **Adversarial Reporting**: Assign CVSS (Common Vulnerability Scoring System) scores to findings.
5.  **Remediation**: Propose and execute surgical code fixes to close identified gaps.

## Guardrails
- **Non-Destructive**: Red-Teaming simulations must NEVER modify production data or permanent system configurations.
- **PII Protection**: Audit logs must be scrubbed of any user-sensitive data before being stored in Axis 11.
- **Resource Budget**: Simulations must not exceed 2.0 GB VRAM or 5% CPU overhead to maintain system responsiveness.

## Output Format
- `vulnerability_manifest`: List of identified gaps with severity levels.
- `attack_vector`: Description of the simulated exploit path.
- `cvss_score`: Numerical score (0.0 - 10.0) based on impact and exploitability.
- `remediation_plan`: Step-by-step guide to fixing the vulnerability.
