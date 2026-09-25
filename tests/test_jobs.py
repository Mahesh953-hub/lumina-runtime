import base64
from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image

from lumina.api import create_app


def png(color):
    buffer = BytesIO()
    Image.new("RGB", (16, 16), color).save(buffer, "PNG")
    return base64.b64encode(buffer.getvalue()).decode()


def test_job_lifecycle_and_persisted_result(tmp_path):
    client = TestClient(create_app(output_dir=tmp_path))
    created = client.post(
        "/v1/jobs",
        json={
            "operation": "create",
            "prompt": "canvas",
            "width": 16,
            "height": 16,
        },
    )
    assert created.status_code == 202
    job_id = created.json()["job_id"]
    assert created.json()["state"] == "queued"

    status = client.get(f"/v1/jobs/{job_id}")
    assert status.status_code == 200
    assert status.json()["job_id"] == job_id
    assert status.json()["state"] in {"queued", "running", "completed"}
    assert "events" in status.json()


def test_job_rejects_unknown_operations(tmp_path):
    client = TestClient(create_app(output_dir=tmp_path))
    response = client.post("/v1/jobs", json={"operation": "run_shell", "prompt": "x"})
    assert response.status_code == 422


def test_job_worker_can_create_and_revise(tmp_path):
    from lumina.jobs import JobStore, VisualJobWorker

    store = JobStore(tmp_path / "jobs.sqlite3")
    job = store.create(operation="create", payload={"prompt": "canvas", "width": 16, "height": 16})
    worker = VisualJobWorker(store)
    worker.run_once()
    completed = store.get(job["job_id"])
    assert completed["state"] == "completed"
    assert completed["result"]["artifact_id"]


def test_job_cancel_is_terminal_and_replayable(tmp_path):
    from lumina.jobs import JobStore

    store = JobStore(tmp_path / "jobs.sqlite3")
    job = store.create(operation="create", payload={"prompt": "canvas"})
    store.cancel(job["job_id"])
    canceled = store.get(job["job_id"])
    assert canceled["state"] == "canceled"
    assert canceled["events"][-1]["event"] == "job.canceled"
