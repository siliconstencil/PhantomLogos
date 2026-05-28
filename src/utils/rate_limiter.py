"""
TokenBucket Rate Limiter.
Provides thread-safe token bucket rate limiting for local LLM request orchestration.
"""

import threading
import time


class TokenBucket:
    """
    Thread-safe Token Bucket Rate Limiter.
    Allows smooth token consumption with dynamic, time-based replenishment.
    """

    def __init__(self, capacity: float, fill_rate: float) -> None:
        self.capacity = float(capacity)
        self.fill_rate = float(fill_rate)
        self.tokens = float(capacity)
        self.last_update = time.time()
        self._lock = threading.Lock()

    def consume(self, tokens: float) -> bool:
        """
        Consumes the specified number of tokens if available.
        Returns True if successful, False otherwise.
        """
        with self._lock:
            now = time.time()
            elapsed = now - self.last_update
            self.last_update = now

            # Replenish tokens based on elapsed time
            self.tokens = min(self.capacity, self.tokens + elapsed * self.fill_rate)

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def get_tokens(self) -> float:
        """
        Returns the current number of tokens in the bucket (replenished up to now).
        """
        with self._lock:
            now = time.time()
            elapsed = now - self.last_update
            self.tokens = min(self.capacity, self.tokens + elapsed * self.fill_rate)
            return self.tokens
