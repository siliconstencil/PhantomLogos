# Phase 11.19.5: Modular Lachesis Entry Point
# Prevents circular imports by using lazy imports for verifiers.
from typing import Any


def CodebaseMapper(*args: Any, **kwargs: Any) -> Any:  # noqa: N802
    from .mapper import CodebaseMapper as _CodebaseMapper

    return _CodebaseMapper(*args, **kwargs)


def AdversarialEvaluator(*args: Any, **kwargs: Any) -> Any:  # noqa: N802
    from .verifiers import AdversarialEvaluator as _AdversarialEvaluator

    return _AdversarialEvaluator(*args, **kwargs)


def OutputGuard(*args: Any, **kwargs: Any) -> Any:  # noqa: N802
    from .verifiers import OutputGuard as _OutputGuard

    return _OutputGuard(*args, **kwargs)


def get_output_guard(*args: Any, **kwargs: Any) -> Any:
    from .verifiers import get_output_guard as _get_output_guard

    return _get_output_guard(*args, **kwargs)


__all__ = ["AdversarialEvaluator", "CodebaseMapper", "OutputGuard", "get_output_guard"]
