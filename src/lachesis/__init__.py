from typing import Any

# Phase 11.19.5: Modular Lachesis Entry Point
# Prevents circular imports by using lazy imports for verifiers.

def CodebaseMapper(*args, **kwargs):
    from .mapper import CodebaseMapper as _CodebaseMapper
    return _CodebaseMapper(*args, **kwargs)

def AdversarialEvaluator(*args, **kwargs):
    from .verifiers import AdversarialEvaluator as _AdversarialEvaluator
    return _AdversarialEvaluator(*args, **kwargs)

def OutputGuard(*args, **kwargs):
    from .verifiers import OutputGuard as _OutputGuard
    return _OutputGuard(*args, **kwargs)

def get_output_guard(*args, **kwargs):
    from .verifiers import get_output_guard as _get_output_guard
    return _get_output_guard(*args, **kwargs)

__all__ = ["CodebaseMapper", "AdversarialEvaluator", "OutputGuard", "get_output_guard"]
