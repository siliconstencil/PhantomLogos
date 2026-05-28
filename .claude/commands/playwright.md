# Playwright Browser Automation

Run browser automation, E2E tests, or web scraping using the Playwright MCP server.

## Steps

1. **Navigate** — Call `playwright_navigate` with the target URL. Always navigate before any interaction.

2. **Interact** — Use appropriate tools:
   - `playwright_click` / `playwright_fill` / `playwright_select` for form flows
   - `playwright_press_key` for keyboard input (Enter, Tab, Escape, ArrowDown)
   - `playwright_hover` / `playwright_drag` for pointer interactions
   - `playwright_iframe_click` / `playwright_iframe_fill` for iframe content

3. **Extract** — Capture page state:
   - `playwright_get_visible_text` for readable content
   - `playwright_get_visible_html` for raw HTML
   - `playwright_screenshot` for visual documentation
   - `playwright_console_logs` for JS errors and debug output

4. **Assert** — Validate responses:
   - `playwright_expect_response` + `playwright_assert_response` for API calls
   - `playwright_evaluate` for JS expression evaluation (trusted code only)

5. **Cleanup** — Call `playwright_close` when done to release browser resources.

## Codegen Mode

To record a test session:
```
start_codegen_session(outputPath) -> interact manually -> end_codegen_session(sessionId)
```

## Guardrails
- Never use `playwright_evaluate` with untrusted JavaScript.
- Always call `playwright_close` after completing a session.
- For API-only tasks, use `playwright_get`/`playwright_post` directly without browser launch.
- Prefer `playwright_screenshot` for debugging visual regressions.

Task or URL: $ARGUMENTS
