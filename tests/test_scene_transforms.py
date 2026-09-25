from lumina.scenes import Scene, SceneValidationError


def test_scene_accepts_opacity_and_rotation(tmp_path):
    scene = Scene(
        width=32,
        height=32,
        layers=[
            {"id": "box", "type": "rectangle", "box": [0, 0, 8, 8], "opacity": 0.5, "rotation": 90}
        ],
    )
    assert scene.export(tmp_path / "scene.png").exists()


def test_scene_rejects_invalid_transform():
    try:
        Scene(
            width=32,
            height=32,
            layers=[{"id": "box", "type": "rectangle", "box": [0, 0, 8, 8], "opacity": 2}],
        )
    except SceneValidationError:
        pass
    else:
        raise AssertionError("expected SceneValidationError")
