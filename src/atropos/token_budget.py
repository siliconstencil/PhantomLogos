import json
import threading
import time

from src.utils.logging_config import setup_logger

SECONDS_IN_DAY = 86400
SECONDS_IN_HOUR = 3600

DEFAULT_DAILY_LIMIT = 100_000
DEFAULT_HOURLY_LIMIT = 10_000

logger = setup_logger(__name__)


class TokenBudgetGuard:
    """
    Real-time token budget monitor.
    Tracks cumulative tokens used and enforces per-session limits.
    Persists to Axis 4 (TemporalStore) for cross-session continuity [SRC:axis_4].
    """

    def __init__(
        self,
        daily_limit: int = DEFAULT_DAILY_LIMIT,
        hourly_limit: int = DEFAULT_HOURLY_LIMIT,
        session_id: str = "default",
    ) -> None:
        self.session_id = session_id
        self.daily_limit = daily_limit
        self.hourly_limit = hourly_limit
        self._daily_used = 0
        self._hourly_used = 0
        self._daily_reset = time.time() + SECONDS_IN_DAY
        self._hourly_reset = time.time() + SECONDS_IN_HOUR
        self._lock = threading.Lock()
        self._persist_counter = 0
        self._load_from_store()

    def _load_from_store(self) -> None:
        try:
            from cognition.mnemosyne.temporal_store import TemporalStore

            store = TemporalStore()
            rows = store.query(
                session_id=self.session_id,
                event_type="token_budget",
                limit=1,
            )
            if rows:
                meta = rows[0].get("metadata", "{}")
                if isinstance(meta, str):
                    meta = json.loads(meta)
                if isinstance(meta, dict):
                    self._daily_used = meta.get("daily_used", 0)
                    self._hourly_used = meta.get("hourly_used", 0)
                    logger.info(
                        f"TokenBudgetGuard: Restored daily={self._daily_used}, "
                        f"hourly={self._hourly_used} from TemporalStore"
                    )
        except Exception as e:
            logger.debug(f"TokenBudgetGuard: restore skipped ({e})")

    def _persist(self) -> None:
        try:
            from cognition.mnemosyne.temporal_store import TemporalStore

            store = TemporalStore()
            store.record_with_supersede(
                session_id=self.session_id,
                event_type="token_budget",
                event_key=f"token_budget_{self.session_id}",
                tokens_used=self._daily_used + self._hourly_used,
                extra={
                    "daily_used": self._daily_used,
                    "hourly_used": self._hourly_used,
                    "daily_limit": self.daily_limit,
                    "hourly_limit": self.hourly_limit,
                },
            )
        except Exception as e:
            logger.debug(f"TokenBudgetGuard: persist skipped ({e})")

    def _check_reset(self) -> None:
        now = time.time()
        if now >= self._daily_reset:
            self._daily_used = 0
            self._daily_reset = now + SECONDS_IN_DAY
            self._persist()
        if now >= self._hourly_reset:
            self._hourly_used = 0
            self._hourly_reset = now + SECONDS_IN_HOUR
            self._persist()

    def consume(self, tokens: int) -> bool:
        with self._lock:
            self._check_reset()
            if self._daily_used + tokens > self.daily_limit:
                return False
            if self._hourly_used + tokens > self.hourly_limit:
                return False
            self._daily_used += tokens
            self._hourly_used += tokens
            self._persist_counter += 1
            if self._persist_counter % 10 == 0:
                self._persist()
            return True

    def remaining_daily(self) -> int:
        with self._lock:
            self._check_reset()
            return max(0, self.daily_limit - self._daily_used)

    def remaining_hourly(self) -> int:
        with self._lock:
            self._check_reset()
            return max(0, self.hourly_limit - self._hourly_used)

    def status(self) -> dict:
        with self._lock:
            self._check_reset()
            return {
                "daily_used": self._daily_used,
                "daily_remaining": max(0, self.daily_limit - self._daily_used),
                "hourly_used": self._hourly_used,
                "hourly_remaining": max(0, self.hourly_limit - self._hourly_used),
            }


_GLOBAL_GUARD: TokenBudgetGuard | None = None
_init_lock = threading.Lock()


def get_token_guard(daily_limit: int = 100_000) -> TokenBudgetGuard:
    global _GLOBAL_GUARD
    with _init_lock:
        if _GLOBAL_GUARD is None:
            _GLOBAL_GUARD = TokenBudgetGuard(daily_limit=daily_limit)
    return _GLOBAL_GUARD
