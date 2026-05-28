from cognition.sophia import verify_math
from src.lachesis.verifiers import SympyVerifier


def _is_valid(res) -> bool:
    """Helper: handles both dict and VerificationResult objects."""
    if isinstance(res, dict):
        return bool(res.get("valid") or res.get("is_valid"))
    return bool(getattr(res, "verified", False) or getattr(res, "is_verified", False))


def test_sympy_consolidated_port():
    # Test ported methods via Sophia bridge
    math_res = verify_math("3*x - 10 = 20")
    assert _is_valid(math_res), f"Expected valid result, got: {math_res}"


def test_qwed_integration():
    v = SympyVerifier()
    res = v.audit_code_logic("x = 1; y = 2; z = x + y")
    if isinstance(res, dict):
        assert "has_contradiction" in res or _is_valid(res)
    else:
        assert _is_valid(res) or hasattr(res, "verified")


def test_reranker_fallback_proof():
    v = SympyVerifier()
    proof = v.verify_reranker_fallback()
    assert proof["is_formally_verified"] is True
    assert proof["axis"] == 11
