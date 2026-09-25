from lumina.runtime import QuotaPolicy, RuntimeMetrics


def test_metrics_count_operations():
    metrics = RuntimeMetrics()
    metrics.increment("create")
    metrics.increment("create")
    assert metrics.snapshot() == {"create": 2}


def test_quota_policy_blocks_over_limit():
    policy = QuotaPolicy(2)
    assert policy.allow(0) is True
    assert policy.allow(2) is False
