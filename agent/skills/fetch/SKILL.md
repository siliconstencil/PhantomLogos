---
name: fetch
description: Web page fetching and content extraction via Fetch MCP server. Fetches URLs with markdown conversion, readability mode, and robots.txt compliance.
version: 1.0.0
license: MIT
compatibility: opencode
model_role: primary
allowed_tools:
  - fetch_fetch
  - report
tier: 2
when_to_use:
  - Fetching web pages for research, documentation, or reference.
  - Extracting readable content from articles or documentation sites.
  - Any task requiring up-to-date information from the web.
metadata:
  audience: developers
  tier: L2-Executor
  workflow: research
---

# Skill: Fetch MCP

Web fetching with content extraction, markdown conversion, and robots.txt compliance. Replaces ad-hoc web scraping with a standardized MCP tool.

## Tool Interface

`fetch_fetch` accepts:
- `url`: Target URL to fetch
- `max_length`: Maximum returned content length (default: 5000)
- `raw`: If true, return raw HTML instead of markdown (default: false)
- `start_index`: Character offset for paginated fetches (default: 0)

## Capabilities

- **Markdown Conversion**: HTML-to-markdown via markdownify
- **Readability Mode**: Content extraction via readabilipy (removes boilerplate)
- **Robots.txt Compliance**: Respects robots.txt via protego
- **Content Truncation**: Respects `max_length` parameter
- **Pagination**: Use `start_index` for multi-page fetches

## Guardrails

- ALWAYS respect robots.txt (enforced by the server)
- Prefer readability mode for articles and docs
- Use `max_length` conservatively (5000 is usually sufficient)
- For large pages, paginate with `start_index`
