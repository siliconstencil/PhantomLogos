import hashlib
import hmac
import json
import os

from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)


def get_a2a_secret(agent_id: str) -> str:
    """
    Retrieve the A2A secret key for a specific agent.
    Falls back to a default secret and logs a warning if not configured in the environment.
    """
    env_var_name = f"A2A_SECRET_{agent_id.upper()}"
    secret = os.getenv(env_var_name)
    if not secret:
        default_secret = os.getenv("A2A_SECRET_DEFAULT", "default_secret_key_12345")
        logger.warning(
            f"A2A Auth: No secret found for agent '{agent_id}' under environment variable '{env_var_name}'. "
            f"Using default fallback secret."
        )
        return default_secret
    return secret


def sign_payload(payload: dict, secret: str) -> str:
    """
    Sign a dictionary payload using HMAC-SHA256 with deterministic JSON formatting.
    """
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hmac.new(secret.encode("utf-8"), serialized.encode("utf-8"), hashlib.sha256).hexdigest()


def verify_signature(payload: dict, secret: str, signature: str) -> bool:
    """
    Verify an HMAC-SHA256 signature against a dictionary payload.
    """
    if not signature:
        return False
    expected = sign_payload(payload, secret)
    return hmac.compare_digest(expected, signature)
