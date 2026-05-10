# [SRC:axis_8] Lachesis Adversarial Evaluator (Modular)
import re
import json
from typing import Dict, Any, List
from src.utils.logging_config import setup_logger
from cognition.mnemosyne.session_log import SessionLog
from .base import SympyVerifier

logger = setup_logger(__name__)

BOILERPLATE_PATTERNS = [
    r"print\(['\"]hello",
    r"#\s*TODO",
    r"pass\s*$",
    r"return\s+None\s*$",
]
QUALITY_PATTERNS = [
    r"def\s+\w+.*->.*:",
    r"\"\"\".*\"\"\"",
    r"try\s*:",
    r"raise\s+\w+Error",
    r"@\w+",
    r"class\s+\w+",
]
FLAW_PATTERNS = [
    (r"except\s*:", "bare except"),
    (r"import\s+\*", "wildcard import"),
    (r"print\(", "print statement instead of logger"),
    (r"\.\./", "relative path traversal"),
    (r"os\.system", "unsafe os.system call"),
]

class AdversarialEvaluator:
    """
    SOTA 2026 Adversarial QA Layer.
    Uses heuristic analysis + keyword extraction for realistic grading.
    """
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.log = SessionLog(session_id)
        self.verifier = SympyVerifier()

    def _design_score(self, draft: str) -> float:
        lines = [l for l in draft.split("\n") if l.strip()]
        if len(lines) < 5:
            return 0.2
        has_header = any(l.strip().startswith("#") for l in lines)
        has_imports = any(l.strip().startswith("import") or l.strip().startswith("from") for l in lines)
        has_structure = sum(1 for l in lines if l.strip().startswith(("class ", "def ")))
        score = 0.5
        if has_header: score += 0.1
        if has_imports: score += 0.1
        score += min(0.3, has_structure * 0.05)
        return min(1.0, score)

    def _originality_score(self, draft: str) -> float:
        boilerplate_hits = sum(len(re.findall(p, draft, re.MULTILINE)) for p in BOILERPLATE_PATTERNS)
        total_lines = max(1, len(draft.split("\n")))
        ratio = boilerplate_hits / total_lines
        return max(0.2, 1.0 - ratio * 5)

    def _functionality_score(self, draft: str) -> float:
        quality_hits = sum(len(re.findall(p, draft, re.MULTILINE)) for p in QUALITY_PATTERNS)
        has_return = "return" in draft
        has_main = "if __name__" in draft
        score = 0.3 + min(0.4, quality_hits * 0.05)
        if has_return: score += 0.15
        if has_main: score += 0.15
        return min(1.0, score)

    def _craft_score(self, draft: str) -> float:
        flaws_detected = []
        for pattern, flaw_name in FLAW_PATTERNS:
            if re.search(pattern, draft, re.MULTILINE):
                flaws_detected.append(flaw_name)
        lines_count = len(draft.split("\n"))
        density = max(0, 1.0 - len(flaws_detected) * 0.08)
        if lines_count < 3: density = 0.1
        elif lines_count < 10: density = max(density, 0.3)
        return min(1.0, density + 0.1)

    async def evaluate(self, draft: str, contract: dict = None, tool_results: list = None, anchors: str = None) -> dict:
        if not contract: contract = {"threshold": 0.7}
        logger.info(f"Evaluator: Starting adversarial audit for session {self.session_id}")

        if not draft or len(draft.strip()) < 5:
            result = {
                "overall_score": 0.0, "is_pass": False,
                "metrics": {"design": 0.0, "originality": 0.0, "functionality": 0.0, "craft": 0.0, "citation": 0.0, "consistency": 0.0},
                "flaws": ["Draft is empty or too short"], "suggestions": ["Generate more substantial content"]
            }
            self.log.append("evaluator.audit", result)
            return result

        design_score = round(self._design_score(draft), 2)
        originality_score = round(self._originality_score(draft), 2)
        functionality_score = round(self._functionality_score(draft), 2)
        craft_score = round(self._craft_score(draft), 2)
        citation_score = round(self._citation_score(draft), 2)
        consistency_score = round(self._consistency_score(draft, tool_results, anchors), 2)
        ocr_score = round(self._ocr_accuracy_score(draft, tool_results or []), 2)
        verification_score = round(await self._verification_score(draft), 2)

        overall_score = round(
            (design_score * 0.15 + originality_score * 0.05 + functionality_score * 0.15 + 
             craft_score * 0.05 + citation_score * 0.15 + consistency_score * 0.15 +
             ocr_score * 0.10 + verification_score * 0.20), 2
        )

        zone = "ambiguous"
        if overall_score >= 0.7: zone = "green"
        elif overall_score < 0.4: zone = "red"

        threshold = contract.get("threshold", 0.7)
        is_pass = overall_score >= threshold
        if verification_score < 0.5: is_pass = False

        flaws = []
        if verification_score < 0.5: flaws.append(f"Invalid math (Axis 11 score {verification_score} < 0.5)")
        if design_score < 0.5: flaws.append(f"Design weak ({design_score})")
        if functionality_score < 0.5: flaws.append(f"Functionality insufficient ({functionality_score})")
        if citation_score < 0.5: flaws.append("Citation missing or poor ([SRC:axis_N] refs required)")
        if consistency_score < 0.5: flaws.append(f"Consistency/Hallucination risk detected ({consistency_score})")

        suggestions = []
        if citation_score < 0.8: suggestions.append("Add [SRC:axis_N] citations for every claim")
        if not re.search(r"def\s+\w+", draft): suggestions.append("Define at least one function")

        result = {
            "overall_score": overall_score, "is_pass": is_pass, "zone": zone,
            "metrics": {
                "design": design_score, "originality": originality_score, "functionality": functionality_score,
                "craft": craft_score, "citation": citation_score, "consistency": consistency_score,
                "ocr_accuracy": ocr_score, "verification": verification_score,
            },
            "flaws": flaws, "suggestions": suggestions,
        }

        self.log.append("evaluator.audit", result)
        
        if overall_score < 0.5:
            try:
                from cognition.mnemosyne.reflection_store import ReflectionStore
                ReflectionStore().store_failure(
                    error_type="critical_quality_drop",
                    root_cause="; ".join(flaws),
                    prevention_rule=f"Urgent: System quality dropped to {overall_score}. Review: {flaws[0] if flaws else 'General logic integrity'}. [REF:Axis8]",
                    severity=3
                )
            except Exception as e:
                logger.warning(f"evaluator: Critical failure record failed ({e})")

        return result

    def _citation_score(self, draft: str) -> float:
        refs = re.findall(r"\[SRC:axis_\d+\]", draft)
        if not refs: return 0.0
        return min(1.0, 0.5 + len(refs) * 0.15)

    def _consistency_score(self, draft: str, tool_results: list = None, anchors: str = None) -> float:
        if not tool_results and not anchors: return 0.7
        evidence_text = ""
        if tool_results:
            for res in tool_results: evidence_text += str(res.get("output", ""))[:500] + " "
        if anchors: evidence_text += anchors[:1000]

        evidence_words = set(re.findall(r"\w{4,}", evidence_text.lower()))
        if not evidence_words: return 1.0
        draft_words = set(re.findall(r"\w{4,}", draft.lower()))
        if not draft_words: return 0.5
        
        match_ratio = len(draft_words.intersection(evidence_words)) / len(draft_words) if draft_words else 1.0
        if match_ratio >= 0.2: return 1.0
        if match_ratio >= 0.1: return 0.7
        return 0.5

    def _ocr_accuracy_score(self, draft: str, tool_results: list) -> float:
        ocr_outputs = [str(res.get("output", "")) for res in tool_results if "OCR Mode" in str(res.get("prompt", ""))]
        if not ocr_outputs: return 1.0
        source_words = set(re.findall(r"\w{3,}", ocr_outputs[0].lower()))
        if not source_words: return 1.0
        matches = sum(1 for w in source_words if w in draft.lower())
        return min(1.0, 0.3 + (matches / len(source_words)) * 0.7)

    async def _verification_score(self, draft: str) -> float:
        import asyncio
        audit_res = await asyncio.to_thread(self.verifier.audit_code_logic, draft)
        
        # Z3 Logical Consistency
        inequality_exprs = re.findall(r"([a-zA-Z]\s*[><=]=?\s*\d+)", draft)
        if inequality_exprs:
            problem_str = "\n".join(inequality_exprs)
            z3_res = await asyncio.to_thread(self.verifier.verify_logic, problem_str)
            if z3_res.get("result") == "Unsatisfiable":
                logger.warning(f"evaluator: Z3 detected mathematical contradiction: {problem_str}")
                return 0.0
        
        math_score = 1.0
        math_exprs = re.findall(r"(\d+\s*[\+\-\*\/]\s*\d+\s*=\s*\d+)", draft)
        if any(kw in draft.lower() for kw in ["calculate", "solve", "result", "="]) or math_exprs:
            complexity = self.verifier.verify_math_expression(draft)
            if complexity == "simple" and math_exprs:
                for expr in math_exprs:
                    if not self.verifier.verify_math(expr).get("valid"):
                        math_score = 0.0
                        break
            else:
                llm_res = await asyncio.to_thread(self.verifier.verify_math_llm, draft)
                math_score = llm_res.get("confidence", 0.85) if llm_res.get("valid") else 0.4

        v_score = (audit_res.get("logic_score", 1.0) * 0.6 + math_score * 0.4)
        return 0.3 if math_score == 0.0 else v_score
