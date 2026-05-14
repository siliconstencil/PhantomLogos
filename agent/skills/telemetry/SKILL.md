---
name: telemetry
description: Collecting and reporting operational metrics for system performance analysis.
version: 1.0.0
license: MIT
compatibility: opencode
when_to_use:
  - Generating post-session performance reports.
  - Analyzing model latency patterns.
metadata:
  audience: developers
  tier: Morpheus
  workflow: telemetry
---
# Skill: Telemetry (Sovereign Edition)

Provides data-driven insights into the agentic ecosystem's health and operational efficiency.

## Workflow
1.  **Extract**: Query `TemporalStore` (Axis 4) for session-specific metrics (latency, tokens, VRAM).
2.  **Analyze**: Compare current performance against historical benchmarks in `RationalStore` (Axis 10).
3.  **Identify**: Highlight anomalies such as token spikes or critical latency bottlenecks.
4.  **Report**: Generate a structured summary for L0 or system-wide optimization.

## Guardrails
- **PII Shield**: Never include raw user prompts or sensitive session data in telemetry reports.
- **Resource Limit**: Telemetry analysis must not consume more than 0.5GB VRAM or exceed 10s execution time.
- **Accuracy**: Only cite verified data from Mnemosyne; do not hallucinate performance trends.

## Output Format
- `total_tokens`: Integer sum of prompt and completion tokens.
- `avg_latency_ms`: Mean response time across the session.
- `peak_vram_gb`: Maximum memory usage recorded.
- `anomalies`: List of detected performance deviations.
