---
name: sovereign-gateway
description: Local proxy management and Pydantic AI hijack protocols for secure model interaction.
version: 1.1.0
license: MIT
compatibility: opencode
when_to_use:
  - Intercepting and auditing external model requests.
  - Redirecting traffic to local fallback models.
  - Enforcing circuit breaker patterns on failing gateways.
metadata:
  audience: architects
  tier: L1-Sophia
  workflow: connectivity
---
# Skill: Sovereign Gateway

Manages the secure communication bridge between the agent loop and internal/external model providers, implementing JIT interception and local fallback redirection via the SovereignProvider layer.

## Workflow
1.  **Intercept**: Hijack the Pydantic AI request stream via `SovereignProvider` to inject Sovereign OS headers and metadata.
2.  **Audit**: Scan the outgoing payload for PII or security violations (via `security-audit`).
3.  **Route**: Determine if the request should proceed to the cloud gateway (`localhost:32553`) or be redirected to local Tier 2/3 fallbacks.
4.  **Circuit Breaker**: Monitor gateway health; if error rate > 20%, trip the breaker and move to `LocalRuntime` fallback.
5.  **Log**: Record the transaction signature and latency in Axis 7 (Operational Store).

## Guardrails
- **Native Authentication**: All outgoing payloads must include the `antigravity-native` gateway key for local authorization.
- **Latency Cap**: Gateway operations must not add more than 200ms of overhead to the total request lifecycle.
- **Fail-Closed**: By default, the gateway fails-closed for high-integrity tasks to prevent data leaks.

## Output Format
- `gateway_uri`: Address of the active model provider.
- `interception_status`: Boolean indicating if the payload was modified.
- `circuit_status`: Current state (OPEN, CLOSED, HALF-OPEN).
- `request_signature`: Cryptographic hash of the audited payload.
