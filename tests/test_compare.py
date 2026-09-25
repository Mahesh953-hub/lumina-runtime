import base64
from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image

from lumina.api import create_app


def image_base64(color):
    buffer = BytesIO()
    Image.new("RGB", (16, 12), color).save(buffer, "PNG")
    return base64.b64encode(buffer.getvalue()).decode()


def test_compare_identical_images_reports_no_difference(tmp_path):
    client = TestClient(create_app(output_dir=tmp_path))
    response = client.post(
        "/v1/images/compare",
        json={"original_base64": image_base64("red"), "candidate_base64": image_base64("red")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["identical"] is True
    assert body["mismatch_fraction"] == 0
    assert body["mean_absolute_error"] == 0
    assert body["rms_error"] == 0
    assert body["difference_artifact_id"]


def test_compare_changed_images_reports_difference(tmp_path):
    client = TestClient(create_app(output_dir=tmp_path))
    response = client.post(
        "/v1/images/compare",
        json={"original_base64": image_base64("red"), "candidate_base64": image_base64("blue")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["identical"] is False
    assert body["mismatch_fraction"] == 1
    assert body["mean_absolute_error"] > 0
    assert body["difference_artifact_id"]


def test_compare_rejects_malformed_images(tmp_path):
    client = TestClient(create_app(output_dir=tmp_path))
    response = client.post(
        "/v1/images/compare",
        json={"original_base64": "not-base64", "candidate_base64": image_base64("red")},
    )
    assert response.status_code == 400
