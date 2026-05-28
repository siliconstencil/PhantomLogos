---
name: browser-qa
description: Browser-based E2E testing and QA automation using Playwright for web interaction, screenshot comparison, and regression testing.
version: 1.0.0
license: MIT
compatibility: opencode
model_role: primary
allowed_tools:
  - run_code
  - verify
  - report
  - semantic
  - mcp_slm_remember
  - mcp_slm_recall
tier: 2
when_to_use:
  - User requests automated browser testing.
  - E2E regression testing before deployment.
  - Web page interaction and screenshot analysis.
  - Form validation, navigation, and UI flow testing.
metadata:
  audience: developers
  tier: L2-Runner
  workflow: qa
---

# Skill: Browser QA

Browser-based end-to-end test automation using Playwright. Covers web page interaction, screenshot diffing, form validation, and regression test suites. Designed for isolated execution via LightSandbox.

## Workflow

1.  **Test Plan (qa):** Analyze the target web application or page. Identify critical user flows (login, navigation, CRUD operations, form submission). Generate a structured test plan with assertions.

2.  **Script Generation (browse):** Write Playwright test scripts in Python. Each test targets one user flow. Use page objects pattern for maintainability. Include explicit waits and error screenshots.

3.  **Execution:** Run tests via LightSandbox for isolation. Capture screenshots at each critical step. Log results (pass/fail, duration, error traces) to Axis 4 (Temporal Store).

4.  **Reporting (qa-only):** Generate a QA report with visual diffs (baseline vs actual), pass/fail matrix, and regression trends. If tests fail, produce a diagnosis with DOM snapshots and network log excerpts.

## Guardrails
- NEVER run browser tests without LightSandbox isolation.
- ALWAYS set viewport, user-agent, and timeouts explicitly.
- Respect rate limits: max 5 parallel tests to avoid resource exhaustion.
- Clean up browser artifacts (screenshots, traces) after each session.
- For authentication flows, use test credentials only — never production secrets.
- If Playwright is not installed, fall back to a dry-run test plan with manual execution instructions.

## Output Format
- `test_plan`: List of test cases with expected outcomes.
- `execution_report`: Pass/fail matrix with durations and error traces.
- `screenshots`: Baseline vs actual comparison (visual diff).
- `diagnosis`: For failed tests — DOM state, network logs, stack trace.
