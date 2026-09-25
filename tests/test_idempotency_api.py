from fastapi.testclient import TestClient

from lumina.api import create_app


def test_job_idempotency_key_reuses_request(tmp_path):
    client = TestClient(create_app(output_dir=tmp_path))
    body = {"operation": "create", "payload": {"prompt": "canvas"}, "idempotency_key": "key-1"}
    first = client.post("/v1/jobs", json=body)
    second = client.post("/v1/jobs", json=body)
    assert first.status_code == second.status_code == 202
    assert first.json()["job_id"] == second.json()["job_id"]
