from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field


@dataclass
class CircuitBreaker:
    failure_threshold: int = 3
    recovery_seconds: float = 30.0
    failures: int = 0
    opened_at: float | None = None

    def allow(self) -> bool:
        if self.opened_at is None:
            return True
        if time.monotonic() - self.opened_at >= self.recovery_seconds:
            self.opened_at = None
            self.failures = 0
            return True
        return False

    def success(self):
        self.failures = 0
        self.opened_at = None

    def failure(self):
        self.failures += 1
        if self.failures >= self.failure_threshold:
            self.opened_at = time.monotonic()


@dataclass
class IdempotencyStore:
    responses: dict[str, dict] = field(default_factory=dict)

    def get_or_create(self, key: str) -> tuple[dict, bool]:
        if key not in self.responses:
            self.responses[key] = {"request_id": uuid.uuid4().hex, "key": key}
            return self.responses[key], True
        return self.responses[key], False
