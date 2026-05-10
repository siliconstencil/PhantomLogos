import time
import threading
from typing import Optional


# Time constants in seconds
SECONDS_IN_DAY = 86400
SECONDS_IN_HOUR = 3600

# Default Budget Limits
DEFAULT_DAILY_LIMIT = 100_000
DEFAULT_HOURLY_LIMIT = 10_000

class TokenBudgetGuard:
    """
    Real-time token budget monitor.
    Tracks cumulative tokens used and enforces per-session limits.
    Designed to replace LangSmith cloud dependency with local control.
    """
    def __init__(self, daily_limit: int = DEFAULT_DAILY_LIMIT, hourly_limit: int = DEFAULT_HOURLY_LIMIT):
        self.daily_limit = daily_limit
        self.hourly_limit = hourly_limit
        self._daily_used = 0
        self._hourly_used = 0
        self._daily_reset = time.time() + SECONDS_IN_DAY
        self._hourly_reset = time.time() + SECONDS_IN_HOUR
        self._lock = threading.Lock()

    def _check_reset(self):
        now = time.time()
        if now >= self._daily_reset:
            self._daily_used = 0
            self._daily_reset = now + SECONDS_IN_DAY
        if now >= self._hourly_reset:
            self._hourly_used = 0
            self._hourly_reset = now + SECONDS_IN_HOUR

    def consume(self, tokens: int) -> bool:
        with self._lock:
            self._check_reset()
            if self._daily_used + tokens > self.daily_limit:
                return False
            if self._hourly_used + tokens > self.hourly_limit:
                return False
            self._daily_used += tokens
            self._hourly_used += tokens
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
        return {
            "daily_used": self._daily_used,
            "daily_remaining": self.remaining_daily(),
            "hourly_used": self._hourly_used,
            "hourly_remaining": self.remaining_hourly(),
        }


_GLOBAL_GUARD: Optional[TokenBudgetGuard] = None
_init_lock = threading.Lock()


def get_token_guard(daily_limit: int = 100_000) -> TokenBudgetGuard:
    global _GLOBAL_GUARD
    with _init_lock:
        if _GLOBAL_GUARD is None:
            _GLOBAL_GUARD = TokenBudgetGuard(daily_limit=daily_limit)
    return _GLOBAL_GUARD
