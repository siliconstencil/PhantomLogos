from typing import Dict, Any, Optional, List
from src.utils.logging_config import setup_logger
from cognition.mnemosyne.meta_cognition import MetaCognitionStore
from src.architrave.model_registry import ROLE_TO_MODEL, get_vram_requirement

logger = setup_logger(__name__)

class SelfTuner:
    """
    Lachesis Self-Tuning Engine.
    Analyzes Meta-Cognition (Axis 8) data to suggest or apply model/routing optimizations.
    """
    def __init__(self):
        self.meta_store = MetaCognitionStore()
        self.failure_threshold = 0.3

    def analyze_agent_performance(self, agent_id: str) -> Dict[str, Any]:
        experience = self.meta_store.get_experience(agent_id)
        if not experience:
            return {"status": "no_data", "suggestions": []}
        suggestions = []
        for rec in experience:
            success_rate = rec.get("success_rate", 1.0)
            pattern = rec.get("task_pattern", "general")
            if success_rate < (1.0 - self.failure_threshold):
                logger.warning(f"SelfTuner: High failure rate for {agent_id}/{pattern} ({success_rate:.2f})")
                suggestion = self._suggest_model_change(agent_id, pattern)
                if suggestion:
                    suggestions.append(suggestion)
        return {"agent_id": agent_id, "status": "analyzed", "suggestions": suggestions}

    def _suggest_model_change(self, agent_id: str, pattern: str) -> Optional[Dict[str, Any]]:
        return {
            "type": "model_rotation",
            "reason": "high_failure_rate",
            "agent_id": agent_id,
            "pattern": pattern,
            "recommendation": "Rotate to next stable model in ROLE_TO_MODEL fallback chain"
        }

    def apply_rotation(self, session_id: str, agent_id: str, reason: str):
        from src.clotho.krisis import blacklist_model

        role = "draft" if agent_id == "sophia" else agent_id
        current_model = ROLE_TO_MODEL.get(role, {}).get("primary")

        if current_model:
            logger.error(f"SelfTuner: Applying rotation for {agent_id} due to: {reason}")
            blacklist_model(session_id, current_model)
            try:
                from src.clotho.bootstrap import get_loader
                get_loader().flush()
            except Exception:
                pass

    def get_best_model_for_role(self, role: str, agent_id: Optional[str] = None) -> str:
        target_agent = agent_id or role
        experience = self.meta_store.get_experience(target_agent)
        best_model = None
        if experience:
            experience = sorted(
                experience,
                key=lambda x: (x.get("success_rate", 0), x.get("avg_quality", 0)),
                reverse=True
            )
            best_model = experience[0].get("best_model")
        if not best_model:
            from src.architrave.model_registry import resolve_local_model
            best_model = resolve_local_model(role, "primary")
            logger.debug(f"SelfTuner: No best_model for {target_agent}, falling back to registry primary: {best_model}")
        return best_model

if __name__ == "__main__":
    tuner = SelfTuner()
    report = tuner.analyze_agent_performance("sophia")
    print(f"Self-Tuner Analysis for Sophia: {report}")
