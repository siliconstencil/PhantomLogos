import asyncio
import re
from typing import Any

from cognition.sophia.eidos import ConstraintValidationResult, ConstraintViolation
from src.architrave import GatewayArchitrave
from src.utils.logging_config import setup_logger

from .koinonia import record_step

logger = setup_logger(__name__)

_gateway_instance = None


def get_gateway():
    global _gateway_instance
    if _gateway_instance is None:
        _gateway_instance = GatewayArchitrave()
    return _gateway_instance


async def extract_logic_llm(draft: str) -> str:
    """
    [SRC:axis_11] Uses Phi-4 Mini to extract logical assertions in SMT-LIB2 format from a draft.
    [HH:MM AM/PM PT]
    """
    try:
        from src.architrave.model_registry import resolve_local_model
        from src.utils.ollama_utils import get_ollama_client

        prompt = f"""Analyze the following technical implementation or text.
Extract any logical claims, constraints, or assertions.
Convert them into a single valid SMT-LIB2 script for the Z3 solver.
Draft: {draft}

Rules:
- Define necessary constants/variables (Bool, Real, or Int).
- Use (assert ...) for each claim.
- End with (check-sat).
- Provide ONLY the SMT-LIB2 code. No markdown tags or explanation.
SMT-LIB2:"""

        client = get_ollama_client()
        model = resolve_local_model("critique", "primary")
        resp = await asyncio.wait_for(client.generate(model=model, prompt=prompt), timeout=30.0)
        return (resp.response or "").strip().replace("```smt2", "").replace("```", "")
    except Exception as e:
        logger.warning(f"deigma: Logic extraction failed ({e})")
        return ""


async def verify_node(state: Any):
    """
    [SRC:axis_6/11] Neuro-Symbolic Verification Hook.
    Implements QWED 2-pass code audit, Qwen Math LLM, and Z3 SAT bridge. [HH:MM AM/PM PT]
    """
    draft = state.get("draft", "")
    retry_count = state.get("verification_retry", 0)

    def sync_verify(draft, retry_count):
        if not draft or len(draft.strip()) < 10:
            return {"verification_retry": retry_count + 1, "memory_sync": True}

        from src.lachesis import get_output_guard
        from src.lachesis.verifiers import SympyVerifier
        from src.lachesis.verifiers.llm_engine import LLMMathEngine
        from src.lachesis.verifiers.qwed_engine import QWEDEngine

        SympyVerifier()  # Legacy support
        qwed = QWEDEngine()
        LLMMathEngine()
        guard = get_output_guard()

        # Step 1: OutputGuard (BA-01 & Safety)
        guard_result = guard.check(draft, agent_id="verify_node")
        if guard_result.get("action") == "reject":
            return {"draft": "", "verification_retry": retry_count + 1, "memory_sync": False}

        # Step 2: QWED 2-Pass Code Audit [TIER 1.1/1.3 FIX]
        audit = qwed.audit_code_logic(draft)
        # [SRC:axis_11] logic_score < 0.6 triggers expert fallback
        if audit.get("logic_score", 1.0) < 0.6:
            logger.info("deigma: Low logic_score detected. Triggering QWED expert fallback...")
            from src.architrave.model_registry import get_qwed_models

            qwed_expert = QWEDEngine(model=get_qwed_models()["fallback"])
            audit = qwed_expert.audit_code_logic(draft)
        # Set audit_fail based on logic_score after expert fallback
        if audit.get("logic_score", 0.0) < 0.6 or not audit.get("is_valid", False):
            audit["audit_fail"] = True
        return audit

    # Core checks in sync pool (BA-01 & QWED)
    results = await asyncio.to_thread(sync_verify, draft, retry_count)

    if results and results.get("audit_fail"):
        return {"draft": "", "verification_retry": retry_count + 1, "memory_sync": False}

    # Step 3: Math Verification [TIER 1.4 FIX] - Moved to async body [Phase 1.0.24]
    if re.search(r"[\d\w]+\s*[\+\-\*\/=]\s*[\d\w]+", draft):
        from src.lachesis.verifiers.llm_engine import LLMMathEngine

        math_engine = LLMMathEngine()
        # [Phase 1.0.24] llm_engine is now fully async
        math_res = await math_engine.verify_math_llm(draft)
        if not math_res.get("is_valid"):
            logger.warning(
                f"deigma: Math verification failed: {math_res.get('result', 'Mismatch')}"
            )
            # [Phase 1.0.24] Implementation of Partial Correction instead of total rejection
            return {
                "partial_correction": {
                    "error_type": "axis_11_math",
                    "details": math_res.get(
                        "result", "Mathematical inconsistency detected in Axis 11 audit."
                    ),
                    "hint": "Please review the mathematical steps and ensure all equations are balanced and correct.",
                },
                "verification_retry": retry_count + 1,
                "memory_sync": False,
            }

    await asyncio.to_thread(record_step, state, "verify")
    # Layer 4: Constraint Guardian - Pydantic structured output via response_schema with fallback
    violation_result = None
    try:
        gw = get_gateway()
        if gw.client is not None:
            resp = await asyncio.wait_for(
                gw.generate_async(
                    prompt=f"Analyze the following draft for constraint violations.\nDraft:\n{draft}",
                    system_instruction="You are a constraint validation system. Check the draft against known system constraints: NO_EMOJI (no emoji characters), 7GB VRAM limit, BA-01 Turkish communication for L0, ASCII-only code, and no hallucinated tool calls. Return structured violation results.",
                    response_schema=ConstraintValidationResult,
                    response_mime_type="application/json",
                ),
                timeout=30.0,
            )
            if resp and hasattr(resp, "text") and resp.text:
                validation = ConstraintValidationResult.model_validate_json(resp.text)
                violation_result = validation
    except Exception:
        logger.info("deigma: Gateway constraint validation unavailable, using local fallback...")

    if violation_result is None:
        try:
            from src.architrave.entity_extractor import EntityExtractor

            extractor = EntityExtractor()
            extract_res = await asyncio.to_thread(extractor.extract_unified, draft)

            raw_constraints = [
                e["text"] for e in extract_res.get("entities", []) if e["type"] == "constraint"
            ]
            violations = []
            if raw_constraints:
                for c in raw_constraints:
                    if "emoji" in c.lower() and re.search(r"[\U00010000-\U0010ffff]", draft):
                        violations.append(
                            ConstraintViolation(
                                constraint=c, severity="critical", detail="Emoji detected in output"
                            )
                        )
                    if (
                        "vram" in c.lower()
                        and "7" in c
                        and re.search(r"\b[8-9]\s*GB\b|\b[1-9][0-9]\s*GB\b", draft)
                    ):
                        violations.append(
                            ConstraintViolation(
                                constraint=c, severity="critical", detail="VRAM limit exceeded"
                            )
                        )
            violation_result = ConstraintValidationResult(
                is_valid=len(violations) == 0,
                violations=violations,
                confidence=0.8,
            )
        except Exception as e_guard:
            logger.warning(f"deigma: Constraint Guardian fallback failed ({e_guard})")

    if violation_result and not violation_result.is_valid:
        details = "; ".join(
            f"[{v.severity}] {v.constraint}: {v.detail}" for v in violation_result.violations
        )
        logger.warning(f"deigma: Constraint Guardian REJECTED draft: {details}")
        return {
            "partial_correction": {
                "error_type": "axis_11_constraint",
                "details": details,
                "hint": "Ensure your output strictly follows all system constraints and NO_EMOJI rules.",
            },
            "verification_retry": retry_count + 1,
            "memory_sync": False,
        }

    # Step 4: Z3 SAT Bridge (Async due to LLM extraction) [TIER 1.2 FIX]
    smt_problem = await extract_logic_llm(draft)
    if smt_problem:
        from src.lachesis.verifiers.z3_engine import verify_logic as z3_verify

        z3_res = await z3_verify(smt_problem)
        if not z3_res.get("is_valid", False):
            logger.warning(f"deigma: Z3 Logic UNSAT/Unknown: {z3_res.get('result', 'Error')}")
            return {
                "partial_correction": {
                    "error_type": "axis_11_logic",
                    "details": z3_res.get(
                        "result", "Z3 SMT solver detected logical unsatisfiability."
                    ),
                    "hint": "Check the logical constraints and consistency of assertions.",
                },
                "verification_retry": retry_count + 1,
                "memory_sync": False,
            }

    complexity_score = len(draft) + (len(re.findall(r"\b(def|class|async|import)\b", draft)) * 100)
    suggested_tier = "expert" if complexity_score > 3000 else "standard"

    return {
        "memory_sync": True,
        "verification_retry": retry_count,
        "selected_model_tier": suggested_tier,
    }
    # Fall-through: return at end of function
