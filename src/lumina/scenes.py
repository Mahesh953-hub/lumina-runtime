from __future__ import annotations

import copy
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


class SceneValidationError(ValueError):
    pass


@dataclass
class Scene:
    width: int = 512
    height: int = 512
    background: str = "#ffffff"
    layers: list[dict] = field(default_factory=list)

    def __post_init__(self):
        if not (16 <= self.width <= 2048 and 16 <= self.height <= 2048):
            raise SceneValidationError("scene dimensions must be between 16 and 2048")
        if len(self.layers) > 50:
            raise SceneValidationError("scene supports at most 50 layers")
        ids = set()
        for layer in self.layers:
            self.validate_layer(layer)
            if layer["id"] in ids:
                raise SceneValidationError("layer ids must be unique")
            ids.add(layer["id"])

    @staticmethod
    def validate_layer(layer: dict):
        if not isinstance(layer, dict) or not isinstance(layer.get("id"), str):
            raise SceneValidationError("each layer needs a string id")
        if layer.get("type") not in {"rectangle", "ellipse", "text"}:
            raise SceneValidationError("unsupported scene layer type")
        if layer["type"] in {"rectangle", "ellipse"}:
            box = layer.get("box")
            if (
                not isinstance(box, list)
                or len(box) != 4
                or not all(isinstance(x, int) for x in box)
            ):
                raise SceneValidationError("shape box must be [x0, y0, x1, y1]")
        if layer["type"] == "text" and not isinstance(layer.get("text"), str):
            raise SceneValidationError("text layer needs text")

    def replace_layer(self, layer_id: str, replacement: dict) -> Scene:
        self.validate_layer({**replacement, "id": layer_id})
        for index, layer in enumerate(self.layers):
            if layer["id"] == layer_id:
                new_layers = copy.deepcopy(self.layers)
                new_layers[index] = {**replacement, "id": layer_id}
                return Scene(self.width, self.height, self.background, new_layers)
        raise SceneValidationError("layer not found")

    def render_image(self) -> Image.Image:
        image = Image.new("RGB", (self.width, self.height), self.background)
        for layer in self.layers:
            draw = ImageDraw.Draw(image)
            if layer["type"] in {"rectangle", "ellipse"}:
                color = layer.get("fill", "#000000")
                if layer["type"] == "rectangle":
                    draw.rectangle(layer["box"], fill=color)
                else:
                    draw.ellipse(layer["box"], fill=color)
            else:
                xy = layer.get("xy", [0, 0])
                size = min(200, max(8, int(layer.get("size", 16))))
                draw.text(
                    tuple(xy),
                    layer["text"][:200],
                    fill=layer.get("fill", "#000000"),
                    font=ImageFont.load_default(size=size),
                )
        return image

    def export(self, path: Path | str, format: str = "PNG") -> Path:
        formats = {"PNG", "JPEG", "WEBP"}
        if format.upper() not in formats:
            raise SceneValidationError("supported scene exports are PNG, JPEG, and WEBP")
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        image = self.render_image()
        image.save(target, format=format.upper(), optimize=True)
        return target

    def render(self, path: Path | str) -> Path:
        image = self.render_image()
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        image.save(target, format="PNG", optimize=True)
        return target
