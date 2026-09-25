import os
from collections import Counter
from threading import Lock


class RuntimeMetrics:
    def __init__(self):
        self._lock = Lock()
        self._counts = Counter()

    def increment(self, name: str):
        with self._lock:
            self._counts[name] += 1

    def snapshot(self) -> dict:
        with self._lock:
            return dict(self._counts)


class QuotaPolicy:
    def __init__(self, limit: int | None = None):
        self.limit = limit if limit is not None else int(os.getenv("LUMINA_QUOTA_LIMIT", "1000"))
        if self.limit < 1:
            raise ValueError("quota limit must be positive")

    def allow(self, current: int) -> bool:
        return current < self.limit
