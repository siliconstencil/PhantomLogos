import asyncio
import re

from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)

try:
    from z3 import Solver, sat, unsat

    HAS_Z3 = True
except ImportError:
    HAS_Z3 = False


def verify_logic_sync(smt_problem: str) -> dict:
    """
    Synchronous Z3 SAT solver wrapper.
    [SRC:axis_11] Direct call without asyncio for sync contexts (tests, audit).
    """
    if not HAS_Z3:
        return {"is_valid": False, "error": "Z3 solver not installed", "axis": 11}

    if not smt_problem or not smt_problem.strip():
        return {"is_valid": False, "error": "Empty SMT problem", "axis": 11}

    if "(" not in smt_problem:
        variables = set(re.findall(r"([a-zA-Z]+)", smt_problem))
        smt_lines = [f"(declare-const {var} Int)" for var in variables]
        constraints = re.split(r"[\n;]", smt_problem)
        for c in constraints:
            c = c.strip()
            if not c:
                continue
            c = re.sub(r"\s*(>=|<=|>|<|=)\s*", r" \1 ", c).strip()
            parts = c.split()
            if len(parts) == 3:
                var, op, val = parts
                smt_lines.append(f"(assert ({op} {var} {val}))")
        smt_problem = "\n".join(smt_lines)
        logger.debug(f"Z3: Translated plain text to SMT:\n{smt_problem}")

    try:
        solver = Solver()
        solver.set("timeout", 5000)

        try:
            solver.from_string(smt_problem)
        except Exception as e:
            logger.error(f"Z3: SMT-LIB2 parse failed: {e}")
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


async def verify_logic(smt_problem: str) -> dict:
    """
    Direct Z3 SAT solver using native SMT-LIB2 format.
    [SRC:axis_11] Supports plain text inequalities by auto-wrapping into SMT-LIB2.
    """
    if not HAS_Z3:
        return {"is_valid": False, "error": "Z3 solver not installed", "axis": 11}

    if not smt_problem or not smt_problem.strip():
        return {"is_valid": False, "error": "Empty SMT problem", "axis": 11}

    # Phase 1.0.31: Plain Text to SMT-LIB2 Translation
    if "(" not in smt_problem:
        variables = set(re.findall(r"([a-zA-Z]+)", smt_problem))
        smt_lines = [f"(declare-const {var} Int)" for var in variables]

        # Split by newlines or semicolon
        constraints = re.split(r"[\n;]", smt_problem)
        for c in constraints:
            c = c.strip()
            if not c:
                continue
            # Convert 'x > 10' to '(assert (> x 10))'
            # Standardizing operators
            c = re.sub(r"\s*(>=|<=|>|<|=)\s*", r" \1 ", c).strip()
            parts = c.split()
            if len(parts) == 3:
                var, op, val = parts
                # SMT operators: >, <, >=, <=, =
                smt_lines.append(f"(assert ({op} {var} {val}))")

        smt_problem = "\n".join(smt_lines)
        logger.debug(f"Z3: Translated plain text to SMT:\n{smt_problem}")

    try:
        solver = Solver()
        solver.set("timeout", 5000)

        try:
            solver.from_string(smt_problem)
        except Exception as e:
            logger.error(f"Z3: SMT-LIB2 parse failed: {e}")
            return {"is_valid": False, "error": f"Parse Error: {e}", "axis": 11}

        # Run check in thread to prevent blocking
        status = await asyncio.to_thread(solver.check)
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
