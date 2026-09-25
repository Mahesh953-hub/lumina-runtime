import pytest

from lumina.scenes import Scene, SceneValidationError


def test_scene_exports_svg_and_pdf(tmp_path):
    scene = Scene(
        width=64,
        height=32,
        layers=[{"id": "box", "type": "rectangle", "box": [1, 1, 20, 20], "fill": "#ff0000"}],
    )
    svg = scene.export(tmp_path / "scene.svg", "SVG")
    pdf = scene.export(tmp_path / "scene.pdf", "PDF")
    assert svg.read_text().startswith("<svg")
    assert pdf.read_bytes().startswith(b"%PDF")


def test_scene_rejects_unsupported_export_format(tmp_path):
    scene = Scene(width=32, height=32, layers=[])
    with pytest.raises(SceneValidationError):
        scene.export(tmp_path / "scene.tiff", "TIFF")
