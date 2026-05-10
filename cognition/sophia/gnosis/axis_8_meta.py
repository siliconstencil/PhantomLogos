from typing import Any, Optional
from ..hephaestus import _get_meta, _get_reflection

def _build_axis_8_meta() -> list:
    lines = []
    try:
        rel = _get_meta().get_reliability("sophia")
        lines.append("### MNEMOSYNE AXIS 8 (META-COGNITION/RELIABILITY)")
        lines.append(f"Agent reliability score: {rel:.2f}")
    except Exception: pass
    return lines

async def _build_axis_8_failures(task_hint: str, vec: Optional[Any] = None) -> tuple[list, dict]:
    lines = []
    block_signal = {"block": False, "reason": None}
    try:
        rules = _get_reflection().get_prevention_rules(limit=5)
        if rules:
            lines.append("### MNEMOSYNE AXIS 8 (PREVENTION RULES)")
            for r in rules:
                sev, rec = r.get('severity', 1), r.get('recurrence_count', 1)
                if sev >= 3 and rec >= 3:
                    block_signal["block"] = True
                    block_signal["reason"] = r.get('prevention_rule')
                lines.append(f"- [{r.get('error_type')}] {r.get('prevention_rule')}")
    except Exception: pass
    return lines, block_signal
