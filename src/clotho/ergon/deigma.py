import asyncio
import re
from typing import Any
from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)

async def verify_node(state: Any):
    """
    [SRC:axis_6] Mandatory Post-Draft Verification Hook (Axis 6/11). 
    Hardened against QWED sync blocking and implements 2-pass L3 logic.
    """
    def sync_verify(draft, retry_count):
        if not draft or len(draft.strip()) < 10:
            return {"verification_retry": retry_count + 1, "memory_sync": True}

        from src.lachesis.verifiers import SympyVerifier
        from src.lachesis import get_output_guard
        verifier = SympyVerifier()
        guard = get_output_guard()
        
        def log_rejection(reason):
            try:
                from cognition.mnemosyne.operational_store import OperationalStore
                op_store = OperationalStore()
                op_store.log_event("verify_node.rejection", reason, {"draft_preview": draft[:200]})
            except Exception as e:
                logger.error(f"ergon: log_rejection failed ({e})")

        # Check behavioral constraints (Emoji, Prohibited words, BA-01)
        guard_result = guard.check(draft, agent_id="verify_node")
        if guard_result.get("action") == "reject":
            logger.warning(f"ergon: verify_node REJECTED draft via OutputGuard (Attempt {retry_count + 1})")
            log_rejection("OutputGuard Rule Violation")
            return {"draft": "", "verification_retry": retry_count + 1, "memory_sync": False}

        # Phase 11.18.13: 2-Pass L3 Verification
        # Pass 1: Phi-4 Mini (Default)
        audit = verifier.audit_code_logic(draft)
        
        # [SRC:axis_11] Pass 2: Two-pass verification — Phi-4 Mini to Qwen-7b fallback on low confidence
        if audit.get("confidence", 1.0) < 0.6 and audit.get("has_contradiction"):
            logger.info("ergon: Phi-4 Mini found contradiction with low confidence. Triggering Pass 2 (Qwen-7b)...")
            from src.architrave.model_registry import resolve_local_model
            pass2_model = resolve_local_model("code", "primary")
            verifier_pass2 = SympyVerifier(model=pass2_model)
            audit_pass2 = verifier_pass2.audit_code_logic(draft)
            if not audit_pass2.get("has_contradiction"):
                logger.info("ergon: Qwen-7b cleared the draft. Contradiction overruled.")
                audit["has_contradiction"] = False
            else:
                logger.warning("ergon: Qwen-7b confirmed contradiction.")
        
        math_exprs = re.findall(r"(\d+\s*[\+\-\*\/]\s*\d+\s*=\s*\d+)", draft)
        math_failed = any(not verifier.verify_math(e).get("valid") for e in math_exprs)

        # AXIS 11: Z3 Logic Verification
        logic_blocks = re.findall(r"<LOGIC>(.*?)</LOGIC>", draft, re.DOTALL)
        logic_failed = False
        for lb in logic_blocks:
            res = verifier.verify_logic(lb)
            if res and not res.get("valid", True):
                logger.warning(f"ergon: Z3 Logic check failed: {res.get('error')}")
                logic_failed = True
                break

        if audit.get("has_contradiction") or math_failed or logic_failed:
            logger.warning(f"ergon: verify_node REJECTED draft via Axis 11 (Attempt {retry_count + 1})")
            log_rejection(f"Axis 11 (Audit={audit.get('has_contradiction')}, Math={math_failed}, Logic={logic_failed}) Violation")
            return {"draft": "", "verification_retry": retry_count + 1, "memory_sync": False}
        
        # Calculate complexity to dynamically adjust the tier for subsequent nodes
        complexity_score = len(draft) + (len(re.findall(r"\b(def|class|async|import)\b", draft)) * 100)
        suggested_tier = "expert" if complexity_score > 3000 else "standard"
        
        return {"memory_sync": True, "verification_retry": retry_count, "selected_model_tier": suggested_tier}

    draft = state.get("draft", "")
    retry_count = state.get("verification_retry", 0)
    
    # Offload the entire sync logic to a thread pool to avoid blocking the main event loop
    return await asyncio.to_thread(sync_verify, draft, retry_count)
