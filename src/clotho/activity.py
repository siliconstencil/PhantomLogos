import threading
from typing import Self


class ActivityMonitor:
    _instance = None
    _lock = threading.Lock()
    _active_tools = 0

    def __new__(cls) -> "Self":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def increment(self) -> None:
        with self._lock:
            self._active_tools += 1

    def decrement(self) -> None:
        with self._lock:
            self._active_tools = max(0, self._active_tools - 1)

    @property
    def is_busy(self) -> bool:
        with self._lock:
            return self._active_tools > 0
