from __future__ import annotations

import time
import uuid
from threading import Lock


class RequestTelemetry:
    def __init__(self):
        self.records: list[dict] = []
        self._lock = Lock()

    def record(self, tenant_id: str, operation: str, cost: float = 0.0):
        event = {
            "trace_id": uuid.uuid4().hex,
            "tenant_id": tenant_id,
            "operation": operation,
            "cost": cost,
            "at": time.time(),
        }
        with self._lock:
            self.records.append(event)
        return event

    def total_cost(self, tenant_id: str | None = None):
        with self._lock:
            return sum(
                r["cost"] for r in self.records if tenant_id is None or r["tenant_id"] == tenant_id
            )
