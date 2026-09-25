from lumina.jobs import JobStore, VisualJobWorker


def test_interrupted_running_jobs_are_requeued(tmp_path):
    path = tmp_path / "jobs.sqlite3"
    first = JobStore(path)
    job = first.create(operation="create", payload={"prompt": "canvas"})
    first.update(job["job_id"], "running", event="job.running")

    second = JobStore(path)
    recovered = second.get(job["job_id"])
    assert recovered["state"] == "queued"
    assert recovered["events"][-1]["event"] == "job.requeued"
    completed = VisualJobWorker(second).run_once()
    assert completed is not None
    assert completed["state"] == "completed"
