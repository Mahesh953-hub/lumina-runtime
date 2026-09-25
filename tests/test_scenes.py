import pytest

from lumina.scenes import Scene, SceneValidationError


def test_scene_renders_layers_and_exports_png(tmp_path):
    scene = Scene(
        width=64,
        height=48,
        background="#ffffff",
        layers=[
            {"id": "card", "type": "rectangle", "box": [4, 4, 30, 25], "fill": "#ff0000"},
            {
                "id": "label",
                "type": "text",
                "text": "LUMINA",
                "xy": [8, 30],
                "size": 10,
                "fill": "#000000",
            },
        ],
    )
    result = scene.render(tmp_path / "scene.png")
    assert result.exists()
    assert result.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    assert result.stat().st_size > 0


def test_scene_replaces_only_named_layer(tmp_path):
    scene = Scene(
        width=32,
        height=32,
        layers=[
            {"id": "one", "type": "rectangle", "box": [0, 0, 10, 10], "fill": "#ff0000"},
            {"id": "two", "type": "rectangle", "box": [20, 20, 30, 30], "fill": "#0000ff"},
        ],
    )
    result = scene.replace_layer(
        "two", {"type": "rectangle", "box": [5, 5, 15, 15], "fill": "#00ff00"}
    ).render(tmp_path / "replaced.png")
    assert result.exists()
    assert [layer["id"] for layer in scene.layers] == ["one", "two"]


def test_scene_exports_webp_and_rejects_unsupported_format(tmp_path):
    scene = Scene(width=32, height=32, layers=[])
    assert scene.export(tmp_path / "scene.webp", "WEBP").exists()
    with pytest.raises(SceneValidationError):
        scene.export(tmp_path / "scene.pdf", "PDF")


def test_scene_rejects_invalid_layers():
    with pytest.raises(SceneValidationError):
        Scene(width=32, height=32, layers=[{"id": "bad", "type": "unknown"}])
