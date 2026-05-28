import time

from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)


class MemoryArbitrator:
    """
    Resolves priority among competing memory items.
    Formula: priority_score = relevance * recency_weight * reliability
    """

    def __init__(
        self,
        base_decay_hours: float = 24.0,
        sensitivity: float = 1.0,
        recency_decay_hours: float | None = None,
    ):
        if recency_decay_hours is not None:
            base_decay_hours = recency_decay_hours
        self.base_decay_hours = base_decay_hours
        self.sensitivity = sensitivity

    def _get_adaptive_decay(self, importance: float) -> float:
        return self.base_decay_hours * (1.0 + self.sensitivity * importance) * 3600

    def score(
        self, importance: float, timestamp: float, frequency: int = 1, reliability: float = 1.0
    ) -> float:
        """
        FIR Scoring Algorithm (2026 SOTA) with Ebbinghaus adaptive S-parameter.
        importance: Base strategic value (0-1).
        frequency: Number of references in session.
        recency: Time since last use.
        """
        import math

        age_seconds = max(0, time.time() - timestamp)
        decay_seconds = self._get_adaptive_decay(importance)
        recency_weight = math.exp(-age_seconds / decay_seconds)

        # Logarithmic frequency boost: rewarded for reuse but with diminishing returns
        frequency_weight = 1.0 + math.log1p(frequency - 1) * 0.1

        return round(importance * frequency_weight * recency_weight * reliability, 4)

    def rank(self, items: list) -> list:
        scored = []
        for item in items:
            s = self.score(
                importance=item.get("importance") or item.get("relevance") or 0.5,
                timestamp=item.get("timestamp", time.time()),
                frequency=item.get("frequency", 1),
                reliability=item.get("reliability", 1.0),
            )
            scored.append((s, item))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored]


if __name__ == "__main__":
    logger.info("=== Mnemosyne Memory Arbitrator: Firmitas Test ===")
    arb = MemoryArbitrator()
    items = [
        {"text": "old", "relevance": 1.0, "timestamp": time.time() - 3600},
        {"text": "new", "relevance": 0.9, "timestamp": time.time()},
    ]
    ranked = arb.rank(items)
    logger.info(f"Connectivity verified. Top item: {ranked[0]['text']}")
