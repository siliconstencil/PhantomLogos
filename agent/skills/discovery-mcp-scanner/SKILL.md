---
name: discovery-mcp-scanner
description: ''
version: 1.0.0
license: MIT
compatibility: opencode
model_role: primary
allowed_tools:
- ls
- mapper
- report
- mcp_slm_remember
tier: 2
---
# Discovery MCP Scanner Skill (discovery-mcp-scanner)

## Overview

This skill scans external MCP servers, dynamically discovers all the capabilities/tools they provide, and registers them in the system's `ToolBridge` infrastructure with a safe namespace prefix (`{server_name}_{tool_name}`).

## Architecture Principles

1. **Dynamic Registration**: When a new MCP server is integrated into the system, adding it to `mcp_config.json` is enough, without any change to the code. The scanner engine discovers the server and registers its tools on first startup.

2. **Namespace Isolation**: To prevent collisions, all tools are isolated with the `{server_name}_{tool_name}` template.

3. **Execution Safety**: All discovered tools are subject to the standard RBAC, telemetry and VRAM hygiene (cleanup) checks through `ToolBridge._dispatch`.

## Usage Guide

To add a new MCP server:

1. Update the `mcp_config.json` file or define the environment variables.

2. The server tools will be registered dynamically in the `ToolBridge` class on first trigger and will be directly callable through `_dispatch`.
