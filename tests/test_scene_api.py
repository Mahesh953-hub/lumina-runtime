from fastapi.testclient import TestClient

from lumina.api import create_app


def test_scene_endpoint_renders_and_records_metrics(tmp_path):
    client = TestClient(create_app(output_dir=tmp_path))
    response = client.post(
        "/v1/scenes/render",
        json={
            "width": 32,
            "height": 32,
            "layers": [
                {"id": "box", "type": "rectangle", "box": [2, 2, 20, 20], "fill": "#ff0000"},
                {"id": "title", "type": "text", "text": "LUMINA", "xy": [3, 24], "size": 8},
            ],
        },
    )
    assert response.status_code == 200
    artifact_id = response.json()["artifact_id"]
    assert client.get(f"/v1/artifacts/{artifact_id}").status_code == 200
    assert client.get("/v1/metrics").json()["counts"]["scene.render"] == 1


def test_scene_endpoint_rejects_invalid_layer(tmp_path):
    client = TestClient(create_app(output_dir=tmp_path))
    response = client.post(
        "/v1/scenes/render",
        json={"layers": [{"id": "bad", "type": "run_shell"}]},
    )
    assert response.status_code == 400
