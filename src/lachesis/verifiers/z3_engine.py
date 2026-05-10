import re
from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)

try:
    from z3 import Solver, Bool, Int, Real, sat, unsat, And, Or, Not, Implies
    HAS_Z3 = True
except ImportError:
    HAS_Z3 = False

def verify_logic(problem: str) -> dict:
    """Direct Z3 SAT solver for logical constraints."""
    if not HAS_Z3:
        return {"valid": False, "error": "Z3 solver not installed", "confidence": 0.0}

    try:
        solver = Solver()
        solver.set("timeout", 5000)

        local_ns = {
            "And": And, "Or": Or, "Not": Not, "Implies": Implies,
            "Bool": Bool, "Int": Int, "Real": Real,
        }
        
        vars_found = set(re.findall(r"\b[a-zA-Z][a-zA-Z0-9_]*\b", problem))
        is_math = any(op in problem for op in [">", "<", "=", "+", "-", "*", "/"])
        
        for v in vars_found:
            if v not in local_ns:
                local_ns[v] = Real(v) if is_math else Bool(v)

        lines = [l.strip() for l in problem.split("\n") if l.strip() and not l.strip().startswith("#")]
        if not lines:
            return {"valid": False, "error": "Empty logical problem", "confidence": 0.0}

        for line in lines:
            try:
                from sympy.parsing.sympy_parser import parse_expr
                expr = parse_expr(line, local_dict=local_ns)
                solver.add(expr)
            except Exception as e:
                logger.warning(f"SympyVerifier: Z3 Eval failed for '{line}' ({e})")
                pass

        status = solver.check()
        if status == sat:
            return {"valid": True, "result": "Satisfiable", "model": str(solver.model()), "confidence": 0.95}
        elif status == unsat:
            return {"valid": False, "result": "Unsatisfiable", "confidence": 0.95}
        else:
            return {"valid": False, "result": "Unknown", "confidence": 0.3}
    except Exception as e:
        logger.error(f"Z3 verification failed: {e}")
        return {"valid": False, "error": str(e), "confidence": 0.0}
