import asyncio

from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)

# Phase 11.18.10: Debounce & Lock Separation (Pillar 2/4)
_debounce_timer: asyncio.Task | None = None
_debounce_lock = asyncio.Lock()


async def schedule_remap(changed_file: str) -> None:
    """
    Phase 11.18.10: True Debounce Pattern (Duzeltme 4).
    Cancels previous pending remaps to ensure only the final write triggers a scan.
    """
    global _debounce_timer
    if _debounce_timer and not _debounce_timer.done():
        _debounce_timer.cancel()
        logger.debug("Debounce: Cancelled pending remap for previous file.")

    _debounce_timer = asyncio.create_task(_debounce_remap(changed_file))


async def _debounce_remap(changed_file: str) -> None:
    try:
        # Pillar 3: 1s debounce is sufficient for AST parse
        await asyncio.sleep(1.0)

        async with _debounce_lock:
            # Pillar 2/4: Thread-safe incremental mapping via Hephaestus Singleton
            from cognition.sophia.hephaestus import get_mapper

            mapper = get_mapper()
            await asyncio.to_thread(mapper.remap_file, changed_file)
            logger.info(f"Debounce: Completed incremental remap for {changed_file}")
    except asyncio.CancelledError:
        logger.debug(f"Debounce: Remap for {changed_file} was cancelled.")
    except Exception as e:
        logger.error(f"Debounce: Remap failed for {changed_file} ({e})")
