import json
import logging
import time
from collections import defaultdict, deque
from threading import Lock


class AuditLog:
    def __init__(self):
        self.events: list[dict] = []
        self._lock = Lock()

    def record(self, event: str, **fields):
        with self._lock:
            self.events.append({"event": event, "at": time.time(), **fields})
        logging.getLogger("lumina.audit").info("%s %s", event, json.dumps(fields, default=str))


class RateLimiter:
    def __init__(self, limit=60, window_seconds=60.0):
        self.limit, self.window, self.requests = limit, window_seconds, defaultdict(deque)
        self._lock = Lock()

    def allow(self, tenant: str):
        now = time.monotonic()
        with self._lock:
            queue = self.requests[tenant]
            while queue and now - queue[0] >= self.window:
                queue.popleft()
            if len(queue) >= self.limit:
                return False
            queue.append(now)
            return True
