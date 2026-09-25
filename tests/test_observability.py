import time

from lumina.observability import AuditLog, RateLimiter


def test_rate_limiter_blocks_burst():
    limiter = RateLimiter(limit=2, window_seconds=60)
    assert limiter.allow("tenant")
    assert limiter.allow("tenant")
    assert not limiter.allow("tenant")
    assert limiter.allow("other")


def test_audit_log_records_structured_event():
    log = AuditLog()
    log.record("image.created", artifact_id="a", tenant_id="t")
    assert log.events[0]["event"] == "image.created"
    assert log.events[0]["tenant_id"] == "t"


def test_audit_event_has_timestamp():
    log = AuditLog()
    before = time.time()
    log.record("test")
    assert log.events[0]["at"] >= before
