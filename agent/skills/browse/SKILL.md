---
name: browse
description: Headless browser automation via MCP. Navigate pages, click elements, fill forms, extract text/HTML, run JavaScript.
version: 1.0.0
license: MIT
compatibility: opencode
model_role: light
allowed_tools:
  - mcp_browse_goto
  - mcp_browse_click
  - mcp_browse_fill
  - mcp_browse_text
  - mcp_browse_html
  - mcp_browse_js
  - mcp_browse_wait
  - mcp_browse_press
  - mcp_browse_url
  - mcp_browse_links
tier: 2
when_to_use:
  - Web scraping or content extraction from live pages.
  - UI interaction testing (click flows, form submissions).
  - Screenshot or accessibility verification.
  - Any task requiring a real browser session.
metadata:
  audience: agents
  tier: L2-Clotho
  workflow: browser
  vram_cost: none
---
# Skill: Browse (Headless Browser)

Persistent headless Chromium via Chrome DevTools Protocol. The server daemon
auto-starts on the first tool call (5-15s cold start on Windows). Subsequent
calls within the same session are ~100ms.

VRAM cost: zero. Chromium runs as a separate OS process, independent of the
model layer.

## Session Lifecycle

The daemon persists until explicitly killed or the system reboots. State file:
`~/.gstack/browse.json` (port + auth token). No explicit session management
needed — tools are stateful across calls.

## Tool Reference

| Tool | Args | Description |
|------|------|-------------|
| `mcp_browse_goto` | `url` | Navigate to URL |
| `mcp_browse_click` | `selector` | Click CSS selector |
| `mcp_browse_fill` | `selector`, `value` | Fill input field |
| `mcp_browse_text` | `selector=""` | Get visible text (page or element) |
| `mcp_browse_html` | `selector=""` | Get raw HTML (page or element) |
| `mcp_browse_js` | `expr` | Evaluate JavaScript expression |
| `mcp_browse_wait` | `selector_or_mode` | Wait for element / `--networkidle` / `--load` |
| `mcp_browse_press` | `key` | Press keyboard key (`Enter`, `Tab`, `Escape`) |
| `mcp_browse_url` | — | Return current page URL |
| `mcp_browse_links` | — | List all hyperlinks on page |

## Workflow

1. `mcp_browse_goto` — navigate to target page.
2. `mcp_browse_wait --networkidle` — wait for dynamic content to settle.
3. Extract with `mcp_browse_text` or `mcp_browse_html`.
4. Interact with `mcp_browse_click`, `mcp_browse_fill`, `mcp_browse_press`.
5. Verify with `mcp_browse_url` or `mcp_browse_js`.

## Error Handling

- Tool raises `RuntimeError` on non-zero browse exit codes.
- On timeout (default 30s, 60s for `wait`): `subprocess.TimeoutExpired`.
- First-call cold start can take up to 15s on Windows — retry once before escalating.
- If daemon fails to start: check `BROWSE_BIN` env var points to a valid binary.

## Guardrails

- Never load CAPTCHA-protected pages in automated flows without L0 awareness.
- Do not store credentials via `mcp_browse_fill` without explicit L0 consent.
- Clear browser state between sensitive sessions if needed (L0 must approve).
