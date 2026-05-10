from ...mnemosyne.operational_store import OperationalStore

def _build_axis_7() -> list:
    lines = []
    try:
        op_events = OperationalStore().get_recent_logs(limit=3)
        if op_events:
            lines.append("### MNEMOSYNE AXIS 7 (OPERATIONAL TELEMETRY)")
            for oe in op_events:
                lines.append(f"- [{oe.name}] {oe.message[:100]}")
    except Exception: pass
    return lines
