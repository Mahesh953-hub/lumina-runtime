from fastapi.testclient import TestClient

from lumina.api import create_app


def test_artifact_metadata_and_download_round_trip(tmp_path):
    client = TestClient(create_app(output_dir=tmp_path))
    created = client.post("/v1/images", json={"prompt": "canvas", "width": 32, "height": 24}).json()

    metadata = client.get(f"/v1/artifacts/{created['artifact_id']}")
    assert metadata.status_code == 200
    assert metadata.json()["artifact_id"] == created["artifact_id"]
    assert metadata.json()["width"] == 32
    assert metadata.json()["height"] == 24

    download = client.get(f"/v1/artifacts/{created['artifact_id']}/content")
    assert download.status_code == 200
    assert download.headers["content-type"] == "image/png"
    assert download.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_artifact_lookup_rejects_missing_and_traversal_ids(tmp_path):
    client = TestClient(create_app(output_dir=tmp_path))
    assert client.get("/v1/artifacts/does-not-exist").status_code == 400
    assert client.get("/v1/artifacts/../secret").status_code in {400, 404}
