---
name: discovery-mcp-scanner
description: JIT tool discovery and binding via Model Context Protocol (MCP).
version: 1.0.0
license: MIT
compatibility: opencode
when_to_use:
  - Agent requires a tool not present in its static whitelist.
  - Exploring external system capabilities during initialization.
metadata:
  audience: architects
  tier: L1-Sophia
  workflow: discovery
---
# Skill: Discovery MCP Scanner
Enables the agent to autonomously query MCP servers for relevant tools, bypassing static whitelist limitations when authorized.
