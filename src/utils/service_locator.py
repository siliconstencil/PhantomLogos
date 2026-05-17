"""
Service Locator Pattern for Phantom Logos.
Resolves circular dependencies by providing a central registry for lazy-loaded components.
"""

from typing import Any

from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)

_registry: dict[str, Any] = {}


def register_service(name: str, service: Any):
    """Registers a service instance."""
    _registry[name] = service
    logger.debug(f"ServiceLocator: Registered '{name}'")


def get_service(name: str) -> Any | None:
    """Retrieves a service instance."""
    return _registry.get(name)


def get_meta_store():
    """Lazy loader for MetaCognitionStore (Axis 8)."""
    if "meta_store" not in _registry:
        from cognition.mnemosyne.meta_cognition import MetaCognitionStore

        _registry["meta_store"] = MetaCognitionStore()
    return _registry["meta_store"]


def get_self_tuner():
    """Lazy loader for Lachesis SelfTuner."""
    if "self_tuner" not in _registry:
        from src.lachesis.self_tuner import SelfTuner

        _registry["self_tuner"] = SelfTuner()
    return _registry["self_tuner"]


def get_model_loader():
    """Lazy loader for Morpheus ModelLoader."""
    if "model_loader" not in _registry:
        from cognition.morpheus.loader import ModelLoader

        _registry["model_loader"] = ModelLoader()
    return _registry["model_loader"]


def get_sweeper():
    """Lazy loader for VRAMSweeper."""
    if "sweeper" not in _registry:
        from cognition.morpheus.sweeper import VRAMSweeper

        _registry["sweeper"] = VRAMSweeper()
    return _registry["sweeper"]


def get_bootstrap_loader():
    """Proxy to Clotho Bootstrap singleton loader."""
    import importlib
    _mod = importlib.import_module("src.clotho.bootstrap")
    return _mod.get_loader()


def get_bootstrap_sweeper():
    """Proxy to Clotho Bootstrap singleton sweeper."""
    import importlib
    _mod = importlib.import_module("src.clotho.bootstrap")
    return _mod.get_sweeper()


def get_matryoshka():
    """Lazy loader for MatryoshkaService (Axis 4)."""
    if "matryoshka" not in _registry:
        from src.atropos.matryoshka_service import MatryoshkaService

        _registry["matryoshka"] = MatryoshkaService()
    return _registry["matryoshka"]
