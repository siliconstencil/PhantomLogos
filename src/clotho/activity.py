import threading

class ActivityMonitor:
    _instance = None
    _lock = threading.Lock()
    _active_tools = 0

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ActivityMonitor, cls).__new__(cls)
            return cls._instance

    def increment(self):
        with self._lock:
            self._active_tools += 1

    def decrement(self):
        with self._lock:
            self._active_tools = max(0, self._active_tools - 1)

    @property
    def is_busy(self) -> bool:
        with self._lock:
            return self._active_tools > 0
