import os
import re

from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)

# Keyring is optional, fallback to .env if not available
try:
    import keyring

    HAS_KEYRING = True
except ImportError:
    HAS_KEYRING = False
    logger.warning("security_utils: 'keyring' library not found. Falling back to .env only.")

SERVICE_NAME = "PhantomLogos"


def load_secrets_to_env():
    """
    Loads critical API keys into os.environ.
    Hierarchy:
    1. Windows Credential Manager (keyring)
    2. .env file (os.getenv fallback)
    """
    keys_to_load = ["GATEWAY_API_KEY"]

    for key in keys_to_load:
        # 1. Attempt to load from Keyring
        secret = None
        if HAS_KEYRING:
            try:
                secret = keyring.get_password(SERVICE_NAME, key)
                if secret:
                    os.environ[key] = secret
                    logger.info(f"security_utils: Loaded {key} from Credential Manager.")
            except Exception as e:
                logger.warning(f"security_utils: Failed to read {key} from keyring ({e})")

        # 2. Fallback to .env (os.getenv) if not found in keyring
        if not secret:
            secret = os.getenv(key)
            if secret:
                # Validation (S5.2)
                if key == "GATEWAY_API_KEY" and not validate_cloud_key(secret):
                    logger.warning(
                        f"security_utils: {key} in .env seems invalid (format check failed)."
                    )
                else:
                    os.environ[key] = secret
                    logger.info(f"security_utils: Using {key} from environment/.env (fallback).")

    # Aliasing logic removed for total agnosticism.


def validate_cloud_key(key: str) -> bool:
    """Sovereign gecidi veya bulut saglayici anahtar formatini dogrular (S5.2)."""
    if not key:
        return False
    # Antigravity yerel gecidi veya AIza tabanli bulut anahtarlarini destekler
    if key == "antigravity-native":
        return True
    return bool(re.match(r"^AIza[0-9A-Za-z-_]{35,}$", key))


def set_secret(key: str, value: str) -> bool:
    """Saves a secret to the Credential Manager."""
    if not HAS_KEYRING:
        return False
    try:
        keyring.set_password(SERVICE_NAME, key, value)
        return True
    except Exception as e:
        logger.error(f"security_utils: Failed to save {key} to keyring ({e})")
        return False
