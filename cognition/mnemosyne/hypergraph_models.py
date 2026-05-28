import hashlib
import math
import time
from dataclasses import dataclass, field


@dataclass
class HypernodeRef:
    """[SRC:axis_15] Represents a reference to a node within one of the 14 memory axes."""

    axis_id: int
    entity_type: str
    entity_key: str
    label: str = ""

    def to_node_id(self) -> str:
        """Returns the unique deterministic string representation of the node."""
        return f"axis_{self.axis_id}:{self.entity_type}:{self.entity_key}"

    @classmethod
    def from_node_id(cls, node_id: str, label: str = "") -> "HypernodeRef":
        """Reconstructs a HypernodeRef from a node_id string."""
        parts = node_id.split(":", 2)
        if len(parts) < 3:
            raise ValueError(f"Invalid node_id format: {node_id}")
        axis_str, entity_type, entity_key = parts
        axis_id = int(axis_str.replace("axis_", ""))
        return cls(axis_id=axis_id, entity_type=entity_type, entity_key=entity_key, label=label)


@dataclass
class Hyperedge:
    """[SRC:axis_15] Represents an edge connecting multiple hypernodes with temporal weighting."""

    nodes: list[HypernodeRef]
    relation_type: str
    weight: float = 1.0
    created_at: float = field(default_factory=time.time)
    valid_until: float | None = None
    edge_id: str = ""

    def __post_init__(self):
        if not self.edge_id:
            self.edge_id = self.generate_id()

    def generate_id(self) -> str:
        """Generates a unique deterministic SHA-256 hash for the hyperedge."""
        node_ids = sorted([n.to_node_id() for n in self.nodes])
        raw_str = f"{','.join(node_ids)}:{self.relation_type}"
        return hashlib.sha256(raw_str.encode()).hexdigest()[:16]

    def is_valid(self, current_time: float | None = None) -> bool:
        """Checks if the hyperedge is temporally valid."""
        t = current_time if current_time is not None else time.time()
        return not (self.valid_until is not None and t > self.valid_until)

    def get_decayed_weight(
        self,
        base_decay_hours: float = 24.0,
        sensitivity: float = 1.0,
        current_time: float | None = None,
    ) -> float:
        """[SRC:axis_15] Calculates the decayed Ebbinghaus weight based on edge age and base decay config."""
        t = current_time if current_time is not None else time.time()
        age_seconds = max(0.0, t - self.created_at)
        age_hours = age_seconds / 3600.0

        # Adaptive S-parameter based on initial weight importance
        decay_hours = base_decay_hours * (1.0 + sensitivity * self.weight)
        if decay_hours <= 0:
            return 0.0

        return self.weight * math.exp(-age_hours / decay_hours)
