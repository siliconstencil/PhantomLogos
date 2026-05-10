TEMPERATURE_PROFILES = {
    "draft": 0.4,
    "critique": 0.0,
    "refine": 0.1,
    "code": 0.3,
    "creative": 0.7,
    "router": 0.0,
    "vision": 0.2,
    "chat": 0.5,
}


def get_temperature(role: str) -> float:
    return TEMPERATURE_PROFILES.get(role, 0.3)
