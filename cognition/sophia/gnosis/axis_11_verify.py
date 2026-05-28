# [SRC:axis_11] Verification Status Axis
def _build_axis_11() -> str:
    lines = []
    try:
        from cognition.mnemosyne.reflection_store import ReflectionStore
        from src.lachesis.verifiers.qwed_engine import HAS_QWED
        from src.lachesis.verifiers.z3_engine import HAS_Z3

        lines.append("### MNEMOSYNE AXIS 11 (LOGICAL VERIFICATION)")
        status = f"Active [Sympy: OK, Z3: {'OK' if HAS_Z3 else 'OFF'}, QWED: {'OK' if HAS_QWED else 'OFF'}]"
        lines.append(f"Status: {status}")

        rules = ReflectionStore().get_prevention_rules(limit=3)
        if rules:
            lines.append("Recent failure memory:")
            for r in rules:
                lines.append(
                    f"  - [{r.get('error_type')}] x{r.get('recurrence_count')} (sev={r.get('severity')})"
                )
    except Exception:
        pass
    return "\n".join(lines)
