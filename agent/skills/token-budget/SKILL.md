---
name: token-budget
description: Monitoring and enforcing token usage limits to ensure cost-efficiency
  and performance.
version: 1.1.0
license: MIT
compatibility: opencode
model_role: primary
allowed_tools:
- report
- mcp_slm_remember
- ls
tier: 2
---
# Skill: Token Budget

Ensures sustainable operation by monitoring and limiting token consumption.

## Workflow
1.  **Track**: Calculate tokens for every request/response cycle.
2.  **Evaluate**: Compare against daily (100k) and hourly (10k) soft limits.
3.  **Throttle**: If limits are approached, switch to more efficient models (e.g., Ministral/DeepSeek).
4.  **Report**: Log budget status to the metadata axis (Axis 13).

## Guardrails
- Critical error recovery tasks are exempt from soft throttling.
- Hard limits (Kill-switch) trigger an automatic pause for L0 review.
- Always prefer local model inference (0 token cost) for routine checks.

## Output Format
- Hourly/Daily usage percentage.
- Estimated remaining budget.
- Recommended model tier for next step.
