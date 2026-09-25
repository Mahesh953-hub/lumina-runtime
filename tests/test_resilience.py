from lumina.resilience import CircuitBreaker, IdempotencyStore


def test_circuit_breaker_opens_and_recovers(monkeypatch):
    breaker = CircuitBreaker(failure_threshold=2, recovery_seconds=1)
    assert breaker.allow()
    breaker.failure()
    breaker.failure()
    assert breaker.allow() is False


def test_idempotency_store_reuses_request():
    store = IdempotencyStore()
    first, created = store.get_or_create("key-1")
    second, created_again = store.get_or_create("key-1")
    assert created is True
    assert created_again is False
    assert first == second
