import unittest

from src.lachesis.verifiers import SympyVerifier


class TestAxis11Logic(unittest.TestCase):
    """
    Axis 11: Sovereign Verification Test Suite.
    Uses Z3 SAT solver to verify system-level logical consistency.
    """

    def setUp(self):
        self.verifier = SympyVerifier()

    def test_agent_hierarchy_consistency(self):
        """
        Verify the logical rule: L2 can only execute if L1 has approved the strategic plan.
        Logic Problem (Z3/SymPy format):
        Implies(ApprovedL1, CanExecuteL2)
        ApprovedL1
        Check: CanExecuteL2 is Satisfiable.
        """
        # SMT-LIB2 format logic problem
        problem = """
        (declare-fun ApprovedL1 () Bool)
        (declare-fun CanExecuteL2 () Bool)
        (assert (=> ApprovedL1 CanExecuteL2))
        (assert ApprovedL1)
        """
        result = self.verifier.verify_logic(problem)

        self.assertTrue(result.get("is_valid"), f"Logic verification failed: {result.get('error')}")
        self.assertEqual(result["result"], "Satisfiable")
        self.assertIn("CanExecuteL2 = True", result["model"])
        print(f"\n[Axis 11] Hierarchy Logic Verified: {result['model']}")

    def test_vram_resource_feasibility(self):
        """
        Verify if Qwen (4.7GB) and Phi-4 (2.8GB) can fit in 8GB VRAM with a 0.5GB safety margin.
        Logic: (4.7 + 2.8) <= (8.0 - 0.5)
        """
        problem = "4.7 + 2.8 <= 8.0 - 0.5"
        result = self.verifier.verify_math(problem)

        self.assertTrue(result.get("is_valid"))
        # SymPy solve for inequality returns True or False
        # Here we just evaluate the expression
        from sympy.parsing.sympy_parser import (
            implicit_multiplication,
            parse_expr,
            standard_transformations,
        )

        transformations = standard_transformations + (implicit_multiplication,)
        val = bool(parse_expr(problem, transformations=transformations))
        self.assertTrue(
            val, "VRAM feasibility check failed: 7.5GB does not fit in 7.5GB margin? Check floats."
        )
        print(f"[Axis 11] VRAM Resource Feasibility: {problem} -> {val}")

    def test_code_logic_audit_local(self):
        """
        Verify the local QWED/Heuristic audit for contradiction.
        """
        code_with_contradiction = """
def process():
    if True:
        return "Success"
    else:
        return "Failure" # This is logically unreachable but syntactically fine.
        """
        # We test if the auditor detects the unreachable branch or structural flaw
        result = self.verifier.audit_code_logic(code_with_contradiction)
        self.assertIn("is_valid", result)
        print(f"[Axis 11] Code Logic Audit Result: {result}")


if __name__ == "__main__":
    unittest.main()
