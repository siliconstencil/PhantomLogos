# [SRC:axis_11] Verification Status Axis
def _build_axis_11() -> list:
    lines = []
    try:
        # Use verifiers package instead of old sympy_verifier
        from src.lachesis.verifiers.z3_engine import HAS_Z3
        from src.lachesis.verifiers.qwed_engine import HAS_QWED
        lines.append("### MNEMOSYNE AXIS 11 (LOGICAL VERIFICATION)")
        status = f"Active [Sympy: OK, Z3: {'OK' if HAS_Z3 else 'OFF'}, QWED: {'OK' if HAS_QWED else 'OFF'}]"
        lines.append(f"Status: {status}")
    except Exception: pass
    return lines
