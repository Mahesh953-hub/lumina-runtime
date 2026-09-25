from __future__ import annotations

import time

from .providers import ProviderError


class FailoverImageProvider:
    def __init__(self, providers, attempts: int = 2, retry_delay: float = 0.0):
        if not providers or attempts < 1:
            raise ValueError("at least one provider and one attempt are required")
        self.providers, self.attempts, self.retry_delay = list(providers), attempts, retry_delay

    def generate(self, prompt: str, width: int, height: int):
        last_error = None
        for provider in self.providers:
            for attempt in range(self.attempts):
                try:
                    return provider.generate(prompt, width, height)
                except ProviderError as exc:
                    last_error = exc
                    if attempt + 1 < self.attempts and self.retry_delay:
                        time.sleep(self.retry_delay)
        raise ProviderError("all configured image providers failed") from last_error
