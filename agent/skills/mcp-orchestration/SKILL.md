---
name: mcp-orchestration
description: Autonomously discovers, binds, and orchestrates Model Context Protocol
  (MCP) tools and servers.
version: 1.1.0
license: MIT
compatibility: opencode
model_role: primary
allowed_tools:
- ls
- mapper
- report
- mcp_slm_remember
- mcp_slm_context
tier: 2
---
# Skill: MCP Orchestration (Sovereign Edition)

Autonomously discovers, binds, and orchestrates Model Context Protocol (MCP) tools and servers to extend the system's operational reach.

## Workflow
1.  **JIT Discovery**: Scan the local network and `mcp_registry.json` for active MCP servers.
2.  **Schema Introspection**: Query the discovered servers for tool definitions, resource templates, and prompt schemas.
3.  **Dynamic Binding**: Generate JIT (Just-In-Time) ToolBridge wrappers for the selected MCP tools.
4.  **Verification**: Execute a `dry-run` health check call to ensure the tool responds within the defined latency limits.
5.  **Audit**: Log the discovery and binding event to Axis 10 (Governance Store).

## Guardrails
- **Sandboxing**: All MCP tool executions must occur within the `LightSandbox` layer.
- **Whitelist Only**: Unauthorized MCP servers found during discovery must be flagged and blocked until L0 manual approval.
- **Timeout**: MCP discovery operations must time out after 5 seconds to prevent agentic hangs.
- **Integrity**: Reject any MCP response that does not match the pre-negotiated JSON schema.

## Output Format
- `discovered_servers`: List of active MCP endpoints.
- `bound_tools`: Manifest of tools successfully integrated into the ToolBridge.
- `discovery_status`: Success/Failure indicator with detailed error logs.
- `performance_metrics`: Latency and error rates for the MCP-specific session.
