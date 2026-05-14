from typing import Any

import sympy
from sympy.parsing.sympy_parser import implicit_multiplication, parse_expr, standard_transformations

from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)

# [Phase 1.0.24] Standard transformations for secure math parsing
TRANSFORMATIONS = standard_transformations + (implicit_multiplication,)


def verify_expression(expr_str: str, expected_result: Any = None) -> dict[str, Any]:
    """Verifies if a mathematical string is valid and matches expectation. [HH:MM AM/PM PT]"""
    try:
        # Use parse_expr instead of sympify for better security and implicit multiplication support
        expr = parse_expr(expr_str, transformations=TRANSFORMATIONS)
        result = {
            "is_valid": True,
            "valid": True,  # Backward compatibility alias
            "simplified": str(sympy.simplify(expr)),
            "latex": sympy.latex(expr),
            "axis": 11,
        }
        if expected_result is not None:
            expected = parse_expr(str(expected_result), transformations=TRANSFORMATIONS)
            result["matches_expected"] = bool(sympy.simplify(expr - expected) == 0)

        logger.info(f"SympyVerifier: Expression '{expr_str}' verified.")
        return result
    except Exception as e:
        logger.error(f"SympyVerifier: Verification failed for '{expr_str}' ({e})")
        return {"is_valid": False, "valid": False, "error": str(e), "axis": 11}


def verify_math(problem: str) -> dict[str, Any]:
    """Direct SymPy algebraic solver. Standardized keys. [HH:MM AM/PM PT]"""
    try:
        if "=" in problem and not (">" in problem or "<" in problem or "!=" in problem):
            left_str, right_str = problem.split("=", 1)
            left = parse_expr(left_str.strip(), transformations=TRANSFORMATIONS)
            right = parse_expr(right_str.strip(), transformations=TRANSFORMATIONS)
            eq = sympy.Eq(left, right)
            if eq == False:
                return {
                    "is_valid": False,
                    "valid": False,
                    "error": "Mathematical contradiction",
                    "logic_score": 0.0,
                }
            sol = sympy.solve(eq)
            return {"is_valid": True, "valid": True, "result": str(sol), "logic_score": 0.9}
        else:
            val = parse_expr(problem, transformations=TRANSFORMATIONS)
            if isinstance(val, (bool, sympy.logic.boolalg.BooleanAtom)):
                return {"is_valid": True, "valid": True, "result": str(val), "logic_score": 1.0}
            return {
                "is_valid": True,
                "valid": True,
                "result": str(float(val.evalf())),
                "logic_score": 0.9,
            }
    except Exception as e:
        return {"is_valid": False, "valid": False, "error": str(e), "logic_score": 0.0}


def validate_algebraic_solution(problem: str, proposed_solution: str) -> dict[str, Any]:
    """Validates a proposed solution against the original problem using SymPy. [HH:MM AM/PM PT]"""
    try:
        prob_res = verify_math(problem)
        if not prob_res.get("is_valid"):
            return {
                "is_valid": False,
                "valid": False,
                "error": "Invalid problem structure",
                "logic_score": 0.0,
            }

        try:
            proposed = parse_expr(proposed_solution.strip(), transformations=TRANSFORMATIONS)
            result_str = prob_res.get("result", "")

            if result_str and result_str not in ("[]", "No algebraic problem detected."):
                for sol_str in result_str.replace("[", "").replace("]", "").split(","):
                    sol_str = sol_str.strip()
                    if sol_str:
                        try:
                            expected = parse_expr(sol_str, transformations=TRANSFORMATIONS)
                            if sympy.simplify(proposed - expected) == 0:
                                return {
                                    "is_valid": True,
                                    "valid": True,
                                    "matches": True,
                                    "logic_score": 0.95,
                                }
                        except Exception:
                            continue

            # [TIER 2.2 FIX] matches: False if no match found
            return {
                "is_valid": False,
                "valid": False,
                "matches": False,
                "logic_score": 0.3,
                "error": "Solution mismatch",
            }
        except Exception as e:
            logger.debug(f"SympyVerifier: Proposed solution eval failed ({e})")
            return {
                "is_valid": False,
                "valid": False,
                "error": "Could not evaluate proposed solution",
                "logic_score": 0.0,
            }
    except Exception as e:
        return {"is_valid": False, "valid": False, "error": str(e), "logic_score": 0.0}
