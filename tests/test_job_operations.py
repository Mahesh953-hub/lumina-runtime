from lumina.jobs import JobStore, VisualJobWorker


def encoded_red_png():
    import base64
    from io import BytesIO

    from PIL import Image

    buffer = BytesIO()
    Image.new("RGB", (16, 16), (255, 0, 0)).save(buffer, "PNG")
    return base64.b64encode(buffer.getvalue()).decode()


def test_worker_executes_all_job_operations(tmp_path):
    store = JobStore(tmp_path / "jobs.sqlite3")
    image = encoded_red_png()
    cases = [
        ("create", {"prompt": "canvas", "width": 16, "height": 16}),
        ("analyze", {"image_base64": image}),
        ("compare", {"original_base64": image, "candidate_base64": image}),
        ("edit", {"image_base64": image, "edit_operation": "brighten", "params": {"factor": 0.2}}),
        (
            "revise",
            {"image_base64": image, "instruction": "increase contrast", "max_iterations": 1},
        ),
    ]
    for operation, payload in cases:
        store.create(operation=operation, payload=payload)
        completed = VisualJobWorker(store, tmp_path).run_once()
        assert completed is not None
        assert completed["state"] == "completed"
        assert completed["result"] is not None
