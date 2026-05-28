---
name: playwright
description: Browser automation via Playwright MCP. Full E2E testing with navigation, screenshots, form interaction, multi-tab, file upload, and network interception.
version: 1.0.0
license: MIT
compatibility: opencode
model_role: expert
allowed_tools:
  - playwright_navigate
  - playwright_screenshot
  - playwright_click
  - playwright_fill
  - playwright_select
  - playwright_hover
  - playwright_evaluate
  - playwright_get_visible_text
  - playwright_get_visible_html
  - playwright_console_logs
  - playwright_resize
  - playwright_close
  - playwright_go_back
  - playwright_go_forward
  - playwright_press_key
  - playwright_drag
  - playwright_upload_file
  - playwright_save_as_pdf
  - playwright_click_and_switch_tab
  - playwright_iframe_click
  - playwright_iframe_fill
  - playwright_custom_user_agent
  - playwright_expect_response
  - playwright_assert_response
  - playwright_get
  - playwright_post
  - playwright_put
  - playwright_patch
  - playwright_delete
  - start_codegen_session
  - end_codegen_session
  - get_codegen_session
  - clear_codegen_session
  - report
tier: 3
when_to_use:
  - E2E testing of web applications with real browser interaction.
  - Taking screenshots for documentation, debugging, or visual verification.
  - Web scraping dynamic content (SPA, JS-rendered pages).
  - Form automation, login flows, and multi-step browser workflows.
  - API debugging via browser-based HTTP requests (GET/POST/PUT/PATCH/DELETE).
metadata:
  audience: developers
  tier: L2-Executor
  workflow: testing
---

# Skill: Playwright MCP

Full browser automation via Playwright MCP server. 33 tools covering navigation, interaction, screenshots, code generation, HTTP requests, and multi-tab support. Launches real Chromium/Firefox/Webkit browsers via CDP.

## Tool Categories

### Navigation & Page Control
| Tool | Description |
|------|-------------|
| `playwright_navigate` | Navigate to a URL (chromium/firefox/webkit, viewport control, headless toggle) |
| `playwright_go_back` | Navigate back in browser history |
| `playwright_go_forward` | Navigate forward in browser history |
| `playwright_close` | Close the browser and release resources |
| `playwright_click_and_switch_tab` | Click a link and switch to the newly opened tab |

### Element Interaction
| Tool | Description |
|------|-------------|
| `playwright_click` | Click an element by CSS selector |
| `playwright_fill` | Fill an input field |
| `playwright_select` | Select an option in a `<select>` element |
| `playwright_hover` | Hover over an element |
| `playwright_drag` | Drag element to target location |
| `playwright_press_key` | Press a keyboard key (Enter, ArrowDown, etc.) |
| `playwright_upload_file` | Upload a file to a file input element |

### Iframe Support
| Tool | Description |
|------|-------------|
| `playwright_iframe_click` | Click an element inside an iframe |
| `playwright_iframe_fill` | Fill an input inside an iframe |

### Content Extraction
| Tool | Description |
|------|-------------|
| `playwright_get_visible_text` | Get visible text content of current page |
| `playwright_get_visible_html` | Get HTML content (script removal, minification, length limit) |
| `playwright_screenshot` | Take screenshot (full page, element, base64/PNG) |
| `playwright_save_as_pdf` | Save current page as PDF (A4, Letter, custom margins) |
| `playwright_evaluate` | Execute JavaScript in browser console |

### Network Monitoring
| Tool | Description |
|------|-------------|
| `playwright_expect_response` | Start waiting for an HTTP response by URL pattern |
| `playwright_assert_response` | Wait for and validate expected response |
| `playwright_console_logs` | Retrieve browser console logs (filter by type, search, limit) |

### HTTP Requests (browser context)
| Tool | Description |
|------|-------------|
| `playwright_get` | HTTP GET with bearer token and custom headers |
| `playwright_post` | HTTP POST with body, token, headers |
| `playwright_put` | HTTP PUT with body, token, headers |
| `playwright_patch` | HTTP PATCH with body, token, headers |
| `playwright_delete` | HTTP DELETE with token and custom headers |

### Viewport & Device
| Tool | Description |
|------|-------------|
| `playwright_resize` | Resize viewport (manual dims or 143+ device presets: iPhone, iPad, Pixel, Galaxy) |
| `playwright_custom_user_agent` | Set custom User Agent |

### Code Generation
| Tool | Description |
|------|-------------|
| `start_codegen_session` | Start a Playwright codegen recording session |
| `end_codegen_session` | End session and generate test file |
| `get_codegen_session` | Get session info |
| `clear_codegen_session` | Clear session without generating |

## Workflow: E2E Test

```
navigate(url) -> fill(form) -> click(submit) -> screenshot(result) -> assert_response(api) -> close()
```

## Workflow: Codegen Recording

```
start_codegen_session(outputPath) -> [manual interaction] -> end_codegen_session(sessionId) -> [test file generated]
```

## Guardrails
- Always call `playwright_navigate` first before any page interaction
- Prefer `playwright_screenshot` for visual debugging and documentation
- Use `playwright_close` at the end of each session to free resources
- For multi-step flows, wait between actions with `playwright_get_visible_text` or `playwright_console_logs`
- Never use `playwright_evaluate` for untrusted JavaScript
- For API-only work, prefer the dedicated API tools over browser automation
