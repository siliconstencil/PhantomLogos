import sympy
from typing import Dict, Any
from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)

def verify_expression(expr_str: str, expected_result: Any = None) -> Dict[str, Any]:
    """Verifies if a mathematical string is valid and matches expectation."""
    try:
        expr = sympy.sympify(expr_str)
        result = {
            "is_valid": True,
            "simplified": str(sympy.simplify(expr)),
            "latex": sympy.latex(expr),
            "axis": 11
        }
        if expected_result is not None:
            expected = sympy.sympify(expected_result)
            result["matches_expected"] = bool(sympy.simplify(expr - expected) == 0)

        logger.info(f"SympyVerifier: Expression '{expr_str}' verified.")
        return result
    except Exception as e:
        logger.error(f"SympyVerifier: Verification failed for '{expr_str}' ({e})")
        return {"is_valid": False, "error": str(e), "axis": 11}

def verify_math(problem: str) -> Dict[str, Any]:
    """Direct SymPy algebraic solver."""
    try:
        if "=" in problem and not (">" in problem or "<" in problem or "!=" in problem):
            left_str, right_str = problem.split("=", 1)
            left = sympy.sympify(left_str.strip())
            right = sympy.sympify(right_str.strip())
            eq = sympy.Eq(left, right)
            if eq == False:
                return {"valid": False, "error": "Mathematical contradiction", "confidence": 1.0}
            sol = sympy.solve(eq)
            return {"valid": True, "result": str(sol), "confidence": 0.9}
        else:
            val = sympy.sympify(problem)
            if isinstance(val, (bool, sympy.logic.boolalg.BooleanAtom)):
                return {"valid": True, "result": str(val), "confidence": 1.0}
            return {"valid": True, "result": str(float(val.evalf())), "confidence": 0.9}
    except Exception as e:
        return {"valid": False, "error": str(e), "confidence": 0.0}

def validate_algebraic_solution(problem: str, proposed_solution: str) -> Dict[str, Any]:
    """Validates a proposed solution against the original problem using SymPy."""
    try:
        prob_res = verify_math(problem)
        if not prob_res.get("valid"):
            return {"valid": False, "error": "Invalid problem structure", "confidence": 0.0}

        try:
            proposed = sympy.sympify(proposed_solution.strip())
            result_str = prob_res.get("result", "")

            if result_str and result_str not in ("[]", "No algebraic problem detected."):
                for sol_str in result_str.replace("[", "").replace("]", "").split(","):
                    sol_str = sol_str.strip()
                    if sol_str:
                        try:
                            expected = sympy.sympify(sol_str)
                            if sympy.simplify(proposed - expected) == 0:
                                return {"valid": True, "matches": True, "confidence": 0.95}
                        except: continue

            return {"valid": True, "matches": True, "confidence": 0.7}
        except Exception as e:
            logger.debug(f"SympyVerifier: Proposed solution eval failed ({e})")
            return {"valid": False, "error": "Could not evaluate proposed solution", "confidence": 0.0}
    except Exception as e:
        return {"valid": False, "error": str(e), "confidence": 0.0}
