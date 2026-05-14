from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)

try:
    from z3 import Solver, sat, unknown, unsat

    HAS_Z3 = True
except ImportError:
    HAS_Z3 = False


def verify_logic(smt_problem: str) -> dict:
    """
    Direct Z3 SAT solver using native SMT-LIB2 format.
    [SRC:axis_11] Replaces unreliable SymPy parser with native SMT solver. [HH:MM AM/PM PT]
    """
    if not HAS_Z3:
        return {"is_valid": False, "error": "Z3 solver not installed", "axis": 11}

    if not smt_problem or not smt_problem.strip():
        return {"is_valid": False, "error": "Empty SMT problem", "axis": 11}

    try:
        solver = Solver()
        solver.set("timeout", 5000)

        # Native SMT-LIB2 parsing
        try:
            solver.from_string(smt_problem)
        except Exception as e:
            logger.error(f"Z3: Native SMT-LIB2 parse failed: {e}")
            return {"is_valid": False, "error": f"Parse Error: {e}", "axis": 11}

        status = solver.check()
        if status == sat:
            return {
                "is_valid": True,
                "result": "Satisfiable",
                "model": str(solver.model()),
                "logic_score": 1.0,
                "axis": 11,
            }
        elif status == unsat:
            return {"is_valid": False, "result": "Unsatisfiable", "logic_score": 0.0, "axis": 11}
        else:
            return {"is_valid": False, "result": "Unknown", "logic_score": 0.5, "axis": 11}
    except Exception as e:
        logger.error(f"Z3: verification failed: {e}")
        return {"is_valid": False, "error": str(e), "axis": 11}
