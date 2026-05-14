import json

from ..hephaestus import _get_store


def _build_axis_10(agent_id: str) -> str:
    lines = []
    try:
        rules = _get_store().get_secure_rules(agent_id)
        facts = _get_store().get_secure_facts(agent_id)
        if rules or facts:
            lines.append("### MNEMOSYNE AXIS 10 (RATIONAL/GOVERNANCE)")
            if rules:
                lines.append(f"RULES:\n{json.dumps(rules)}")
            if facts:
                lines.append(f"FACTS:\n{json.dumps(facts)}")
    except Exception:
        pass
    return "\n".join(lines)
