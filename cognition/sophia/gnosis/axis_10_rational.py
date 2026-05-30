import json

from cognition.mnemosyne.hypergraph_feeder import feed_hypergraph

from ..hephaestus import get_store


def _build_axis_10(agent_id: str) -> str:
    lines = []
    try:
        rules = get_store().get_secure_rules(agent_id)
        facts = get_store().get_secure_facts(agent_id)
        if rules or facts:
            lines.append("### MNEMOSYNE AXIS 10 (RATIONAL/GOVERNANCE)")
            if rules:
                lines.append(f"RULES:\n{json.dumps(rules)}")
                if isinstance(rules, list):
                    feed_hypergraph(
                        source_axis_id=10,
                        entities=[
                            {
                                "name": str(r),
                                "type": "rule",
                                "axis_id": 10,
                                "label": "governance_rule",
                            }
                            for r in rules[:5]
                        ],
                        relation_type="governed_by_rule",
                    )
            if facts:
                lines.append(f"FACTS:\n{json.dumps(facts)}")
    except Exception:
        pass
    return "\n".join(lines)
