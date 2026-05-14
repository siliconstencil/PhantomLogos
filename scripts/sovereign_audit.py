import argparse
import ast
import asyncio
import json
import os
import sys
from typing import Any

# [SRC:axis_11] Enforce absolute pathing for Sovereign Auditor [HH:MM AM/PM PT]
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.lachesis.verifiers.qwed_engine import QWEDEngine
from src.lachesis.verifiers.sympy_engine import verify_math
from src.lachesis.verifiers.z3_engine import verify_logic
from src.utils.logging_config import setup_logger

logger = setup_logger("sovereign_audit")


class SovereignAuditor:
    """
    4-Stage Cognitive Chain Auditor.
    [AST] -> [QWED Code] -> [QWED Math/SymPy] -> [Z3 Logic]
    """

    def __init__(self):
        self.qwed = QWEDEngine()

    async def audit(self, code: str, context: str = "") -> dict[str, Any]:
        stages = {}

        # Stage 1: AST Parse (Syntax)
        try:
            ast.parse(code)
            stages["ast"] = {"status": "VALID", "is_valid": True}
        except SyntaxError as e:
            stages["ast"] = {"status": "FAIL", "is_valid": False, "error": str(e)}
            return {"status": "UNSAT", "violations": ["Syntax Error"], "stages": stages}

        # Stage 2: QWED Code Audit (Logic)
        qwed_res = self.qwed.audit_code_logic(code)
        stages["qwed_code"] = qwed_res
        if not qwed_res.get("is_valid"):
            return {"status": "UNSAT", "violations": ["QWED Logic Contradiction"], "stages": stages}

        # Stage 3: Math Verification (SymPy + QWED)
        import re

        # [TIER 4.1 FIX] Refined regex to avoid SMT-LIB2 keywords like declare-const
        math_exprs = re.findall(r"\b\d+\s*[\+\-\*\/=]\s*[\d\w]+", code + "\n" + context)
        math_results = []
        for expr in math_exprs:
            sp_res = verify_math(expr)
            qw_res = self.qwed.verify_math(expr)
            math_results.append(
                {"expr": expr, "sympy": sp_res.get("is_valid"), "qwed": qw_res.get("is_valid")}
            )
            if not sp_res.get("is_valid") or not qw_res.get("is_valid"):
                stages["math"] = {"status": "FAIL", "results": math_results}
                return {
                    "status": "UNSAT",
                    "violations": [f"Math Contradiction: {expr}"],
                    "stages": stages,
                }

        stages["math"] = {"status": "VALID" if math_results else "SKIPPED", "results": math_results}

        # Stage 4: Z3 Formal Verification (Logic)
        if "(assert" in context or "(check-sat)" in context:
            z3_res = verify_logic(context)
            stages["z3"] = z3_res
            if not z3_res.get("is_valid"):
                return {"status": "UNSAT", "violations": ["Z3 SAT Failure"], "stages": stages}
        else:
            stages["z3"] = {"status": "SKIPPED"}

        return {"status": "VALID", "violations": [], "stages": stages}


async def main():
    parser = argparse.ArgumentParser(description="Phantom Logos Sovereign Auditor CLI")
    parser.add_argument("--code", type=str, help="Code string to audit")
    parser.add_argument("--file", type=str, help="File path to audit")
    parser.add_argument(
        "--context", type=str, default="", help="Logical context or SMT-LIB2 script"
    )
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")

    args = parser.parse_args()

    code_to_audit = ""
    if args.file:
        if os.path.exists(args.file):
            with open(args.file, encoding="utf-8") as f:
                code_to_audit = f.read()
        else:
            print(f"Error: File {args.file} not found.")
            sys.exit(1)
    elif args.code:
        code_to_audit = args.code
    else:
        parser.print_help()
        sys.exit(0)

    auditor = SovereignAuditor()
    result = await auditor.audit(code_to_audit, args.context)

    if args.json:
        print(json.dumps(result, indent=4))
    else:
        print(f"\n=== Sovereign Audit Result: {result['status']} ===")
        if result["violations"]:
            print(f"Violations: {', '.join(result['violations'])}")
        for stage, data in result["stages"].items():
            status = data.get("status", "VALID" if data.get("is_valid") else "FAIL")
            print(f"  [{stage.upper()}] {status}")

    sys.exit(0 if result["status"] == "VALID" else 1)


if __name__ == "__main__":
    asyncio.run(main())
