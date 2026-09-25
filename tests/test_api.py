import base64
from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

from lumina.api import create_app


def make_png(color=(255, 0, 0)) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (32, 24), color).save(buffer, "PNG")
    return buffer.getvalue()


def test_health_reports_capabilities(tmp_path: Path):
    client = TestClient(create_app(output_dir=tmp_path))
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "canvas" in response.json()["capabilities"]


def test_create_returns_image_and_observation(tmp_path: Path):
    client = TestClient(create_app(output_dir=tmp_path))
    response = client.post(
        "/v1/images",
        json={"prompt": "a red square on white", "width": 64, "height": 64},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["mime_type"] == "image/png"
    assert body["width"] == 64
    assert len(body["observation"]["dominant_colors"]) >= 1
    image = Image.open(BytesIO(base64.b64decode(body["image_base64"])))
    assert image.size == (64, 64)


def test_analyze_upload_returns_geometry_and_quality(tmp_path: Path):
    client = TestClient(create_app(output_dir=tmp_path))
    response = client.post(
        "/v1/images/analyze",
        files={"image": ("red.png", make_png(), "image/png")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["width"] == 32
    assert body["height"] == 24
    assert body["observation"]["quality"]["brightness"] > 0
    assert body["observation"]["quality"]["contrast"] == 0
    assert body["observation"]["geometry"]["non_background_fraction"] == 0
    assert body["observation"]["geometry"]["content_bbox"] is None


def test_edit_overlay_returns_new_artifact(tmp_path: Path):
    client = TestClient(create_app(output_dir=tmp_path))
    response = client.post(
        "/v1/images",
        json={"prompt": "blue field", "width": 40, "height": 40},
    )
    image = response.json()["image_base64"]
    edit = client.post(
        "/v1/images/edit",
        json={
            "image_base64": image,
            "operation": "draw_rectangle",
            "params": {"box": [0, 0, 20, 20], "fill": [255, 255, 0]},
        },
    )
    assert edit.status_code == 200
    assert edit.json()["revision"] == 2
    assert Image.open(BytesIO(base64.b64decode(edit.json()["image_base64"]))).size == (40, 40)


def test_reject_path_traversal_and_oversized_image(tmp_path: Path):
    client = TestClient(create_app(output_dir=tmp_path))
    response = client.post(
        "/v1/images/analyze",
        files={"image": ("x.png", b"not-an-image", "image/png")},
    )
    assert response.status_code == 400
    assert "decodable" in response.json()["detail"]


def test_openapi_documents_agent_tools(tmp_path: Path):
    client = TestClient(create_app(output_dir=tmp_path))
    schema = client.get("/openapi.json").json()
    assert "/v1/images" in schema["paths"]
    assert "/v1/images/analyze" in schema["paths"]
    assert "/v1/images/edit" in schema["paths"]
