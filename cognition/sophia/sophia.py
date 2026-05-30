import json
import re
from typing import Any

from .telos._gateway import get_gateway
from .telos.critique import run_critique
from .telos.draft import _consecutive_draft_timeouts, run_draft
from .telos.refine import _session_cache_map, run_refine

TEMPERATURE_PROFILES = {
    "draft": 0.1,
    "critique": 0.0,
    "refine": 0.1,
    "code": 0.3,
    "creative": 0.7,
    "router": 0.0,
    "vision": 0.2,
    "chat": 0.5,
}


def get_temperature(role: str) -> float:
    return TEMPERATURE_PROFILES.get(role, 0.1)


class ToolValidator:
    def __init__(self, max_retries: int = 2):
        self.max_retries = max_retries

    def validate_json(self, response: str, required_keys: list = None) -> dict[str, Any]:
        attempt = 0
        last_error = None
        while attempt <= self.max_retries:
            attempt += 1
            try:
                match = re.search(r"\{.*\}", response, re.DOTALL)
                if not match:
                    last_error = ValueError("No JSON block found in response")
                    continue
                data = json.loads(match.group(0))
                if required_keys:
                    missing = [k for k in required_keys if k not in data]
                    if missing:
                        last_error = ValueError(f"Missing required keys: {missing}")
                        continue
                return data
            except json.JSONDecodeError as e:
                last_error = e
        raise last_error or ValueError(f"JSON validation failed after {self.max_retries} attempts")

    def validate_schema(self, data: dict, schema: dict) -> bool:
        for key, expected_type in schema.items():
            if key not in data:
                return False
            if not isinstance(data[key], expected_type):
                return False
        return True


__all__ = [
    "TEMPERATURE_PROFILES",
    "ToolValidator",
    "_consecutive_draft_timeouts",
    "_session_cache_map",
    "get_gateway",
    "get_temperature",
    "run_critique",
    "run_draft",
    "run_refine",
]
