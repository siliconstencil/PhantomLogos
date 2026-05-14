from src.architrave.context_cache import ContextCacheStore


def _build_axis_12() -> str:
    lines = []
    try:
        active_caches = ContextCacheStore().count_active()
        if active_caches > 0:
            lines.append("### MNEMOSYNE AXIS 12 (EFFICIENCY/CACHE)")
            lines.append(f"Active context caches: {active_caches}")
    except Exception:
        pass
    return "\n".join(lines)
