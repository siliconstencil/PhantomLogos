# [SRC:axis_11] Lachesis Output Rule Enforcement (Modular)
import re
from typing import Optional, Dict, Any
from src.utils.logging_config import setup_logger
from .base import SympyVerifier

logger = setup_logger(__name__)

EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF"
    "\U00002702-\U000027B0\U0001F100-\U0001F1FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FAFF\U00002600-\U000026FF\U0000FE00-\U0000FE0F\U0000200D\U0000203C\U00002049"
    "]+", flags=re.UNICODE
)

TURKISH_CHARS = set("\u00e7\u011f\u0131\u00f6\u015f\u00fc\u00c7\u011e\u0130\u00d6\u015e\u00dc")

class OutputGuard:
    """
    Output validation middleware. Scans agent output for rule violations.
    Each violation decrements the agent's reliability score.
    """
    VIOLATION_EMOJI = "emoji_ban"
    VIOLATION_BA01 = "ba01_turkish_chars"
    VIOLATION_NO_TIMESTAMP = "missing_timestamp"
    VIOLATION_VERIFY = "verification_failed"
    VIOLATION_SHADOW_VERIFY = "shadow_verification_failed"
    
    def __init__(self, meta_store=None):
        self._meta = meta_store
        self._violations = {v: 0 for v in [self.VIOLATION_EMOJI, self.VIOLATION_BA01, self.VIOLATION_NO_TIMESTAMP, self.VIOLATION_VERIFY, self.VIOLATION_SHADOW_VERIFY]}
        self._verifier = None

    def _get_verifier(self):
        if self._verifier is None:
            try:
                self._verifier = SympyVerifier()
            except Exception as e:
                logger.warning(f"OutputGuard: SympyVerifier init failed ({e})")
        return self._verifier

    def _verify_output(self, output: str) -> list:
        verifier = self._get_verifier()
        if not verifier: return []
        violations = []
        code_blocks = re.findall(r"```(?:\w+)?\n(.*?)```", output, re.DOTALL)
        for block in code_blocks[:3]:
            if block.strip() and verifier.audit_code_logic(block).get("has_contradiction"):
                violations.append("code_contradiction")
        math_exprs = re.findall(r"(\d+\s*[\+\-\*\/]\s*\d+\s*=\s*\d+)", output)
        for expr in math_exprs[:3]:
            if not verifier.verify_math(expr).get("valid"):
                violations.append(f"invalid_math: {expr}")
        return violations

    def check(self, output: str, agent_id: str = "system", context: Optional[dict] = None) -> dict:
        session_id = context.get("session_id", "default") if context else "default"
        violations = []
        score_delta = 0.0
        
        if EMOJI_PATTERN.findall(output):
            violations.append(self.VIOLATION_EMOJI)
            score_delta -= 0.2
        
        is_user_interaction = context.get("is_user_interaction", False) if context else False
        if not is_user_interaction and any(c in TURKISH_CHARS for c in output):
            violations.append(self.VIOLATION_BA01)
            score_delta -= 0.1
        
        if context and context.get("require_timestamp", False):
            if not re.search(r'\[\d{1,2}:\d{2}\s*(AM|PM)\s*PT\]', output):
                violations.append(self.VIOLATION_NO_TIMESTAMP)
                score_delta -= 0.05

        verify_issues = self._verify_output(output)
        if verify_issues:
            self._violations[self.VIOLATION_VERIFY] += len(verify_issues)
            violations.append(self.VIOLATION_VERIFY if "code_contradiction" in verify_issues else f"{self.VIOLATION_VERIFY}: {verify_issues[0]}")
            score_delta -= 0.3 if "code_contradiction" in verify_issues else 0.15
        
        action = "pass"
        if violations:
            action = "reject" if (self.VIOLATION_EMOJI in violations or self.VIOLATION_VERIFY in violations) else "warn"
            logger.warning(f"OutputGuard [{agent_id}]: Violations {violations}")
            try:
                from cognition.mnemosyne.meta_cognition import MetaCognitionStore
                MetaCognitionStore().adjust_reliability(agent_id=agent_id, delta=score_delta, violation_type=violations[0], session_id=session_id)
            except Exception as e:
                logger.warning(f"OutputGuard: Failed to adjust reliability ({e})")
        
        return {"passed": len(violations) == 0, "violations": violations, "action": action, "score_delta": score_delta}

    def record_shadow_violation(self, agent_id: str, detail: str, session_id: str = "default"):
        logger.error(f"OutputGuard [{agent_id}]: SHADOW VERIFICATION FAILED - {detail}")
        try:
            from cognition.mnemosyne.meta_cognition import MetaCognitionStore
            MetaCognitionStore().adjust_reliability(agent_id=agent_id, delta=-0.3, violation_type=f"{self.VIOLATION_SHADOW_VERIFY}: {detail}", session_id=session_id)
        except Exception as e:
            logger.warning(f"OutputGuard: Failed to record shadow violation ({e})")

_GUARD: Optional[OutputGuard] = None

def get_output_guard(meta_store=None) -> OutputGuard:
    global _GUARD
    if _GUARD is None: _GUARD = OutputGuard(meta_store=meta_store)
    return _GUARD
