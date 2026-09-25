from lumina.telemetry import RequestTelemetry


def test_telemetry_records_trace_and_tenant_cost():
    telemetry = RequestTelemetry()
    event = telemetry.record("tenant-a", "image.create", 0.25)
    assert event["tenant_id"] == "tenant-a"
    assert telemetry.total_cost("tenant-a") == 0.25
    assert telemetry.total_cost("other") == 0
