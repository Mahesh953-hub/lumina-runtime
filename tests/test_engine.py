import base64
from io import BytesIO

import pytest
from PIL import Image

from lumina.engine import MAX_BYTES, UnsafeOperation, VisualEngine


def decode(result):
    return Image.open(BytesIO(base64.b64decode(result.image_base64))).convert("RGB")


def test_canvas_creation_returns_requested_dimensions(tmp_path):
    engine = VisualEngine(tmp_path)
    result = engine.create("a red square on white", 96, 48, "canvas")
    assert decode(result).size == (96, 48)
    assert result.width == 96


def test_revision_loop_improves_canvas_contrast(tmp_path):
    engine = VisualEngine(tmp_path)
    first = engine.create("a red circle", 64, 64, "canvas")
    first_image = decode(first)
    second = engine.revise(first, "increase contrast", max_iterations=1)
    second_image = decode(second)
    assert second.revision == 2
    assert second_image.getextrema() != first_image.getextrema()


def test_draw_text_uses_builtin_font(tmp_path):
    engine = VisualEngine(tmp_path)
    result = engine.create("canvas", 200, 80, "canvas")
    edited = engine.edit(result, "draw_text", {"text": "LUMINA", "xy": [5, 20]})
    assert edited.width == 200
    assert edited.operation == "draw_text"


def test_invalid_edit_does_not_write_artifact(tmp_path):
    engine = VisualEngine(tmp_path)
    with pytest.raises(UnsafeOperation):
        engine.edit_bytes(b"bad", "draw_rectangle", {})
    assert list(tmp_path.iterdir()) == []


def test_decode_rejects_byte_limit_before_image_decode(tmp_path):
    engine = VisualEngine(tmp_path)
    with pytest.raises(UnsafeOperation, match="15 MB"):
        engine._decode(b"x" * (MAX_BYTES + 1))
    assert list(tmp_path.iterdir()) == []
