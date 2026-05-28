# Mnemosyne Write Path

Persist an operational finding, decision, or outcome to the Mnemosyne database following the Sovereign Write Path protocol.

## Core Rule

All persistence flows to `data/mnemosyne.db` — NOT to flat `.md`, `.json`, or `.log` files.

## Write Target Selection

| Finding Type | Store | Axis | MCP Tool |
|---|---|---|---|
| Agent step / decision | EpisodicStore | Axis 1 | `mcp_slm_remember` |
| Tool call and result | ProceduralStore | Axis 2 | `mcp_slm_observe` |
| Objective state change | GoalStore | Axis 3 | `mcp_slm_remember` |
| Fact / governance assertion | RationalStore | Axis 10 | `mcp_slm_remember` |
| Phase outcome | OutcomeStore | Axis 7 | `mcp_slm_report_outcome` |

## Steps

1. **Classify** the content to be written (see table above).
2. **Format** the entry with:
   - Timestamp: `[HH:MM AM/PM PT]`
   - Source citation: `[SRC:axis_N]`
   - Event key: unique identifier for provenance
3. **Write** using the appropriate MCP tool.
4. **Verify** the write succeeded before proceeding.

## Output
- `axis_written`: Which axis received the write
- `event_key`: Identifier assigned to the entry
- `verification_status`: confirmed / failed

Content to persist: $ARGUMENTS
