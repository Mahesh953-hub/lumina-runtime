from fastapi.testclient import TestClient

from lumina.api import create_app


def test_api_key_protects_mutating_routes_when_configured(monkeypatch, tmp_path):
    monkeypatch.setenv("LUMINA_API_KEY", "secret")
    client = TestClient(create_app(output_dir=tmp_path))
    assert client.get("/health").status_code == 200
    assert (
        client.post("/v1/images", json={"prompt": "canvas", "width": 16, "height": 16}).status_code
        == 401
    )
    authorized = client.post(
        "/v1/images",
        json={"prompt": "canvas", "width": 16, "height": 16},
        headers={"X-API-Key": "secret"},
    )
    assert authorized.status_code == 201
