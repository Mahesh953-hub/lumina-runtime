import base64
from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image

from lumina.api import create_app
from lumina.client import LuminaClient


def encoded_red_png():
    buffer = BytesIO()
    Image.new("RGB", (8, 8), (255, 0, 0)).save(buffer, "PNG")
    return base64.b64encode(buffer.getvalue()).decode()


def test_client_wraps_create_compare_and_download(tmp_path, monkeypatch):
    api = create_app(output_dir=tmp_path)
    test_client = TestClient(api)
    monkeypatch.setattr("lumina.client.httpx.Client", lambda **kwargs: test_client)
    with LuminaClient("http://test") as client:
        created = client.create("canvas", 16, 16)
        assert created["width"] == 16
        metrics = client.compare(created["image_base64"], created["image_base64"])
        assert metrics["identical"] is True
        target = client.download(created["artifact_id"], tmp_path / "downloaded.png")
        assert target.read_bytes().startswith(b"\x89PNG")
