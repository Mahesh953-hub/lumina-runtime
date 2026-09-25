from __future__ import annotations

import copy
import html
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
        opacity = layer.get("opacity", 1.0)
        if not isinstance(opacity, (int, float)) or not 0 <= opacity <= 1:
            raise SceneValidationError("layer opacity must be between 0 and 1")
        rotation = layer.get("rotation", 0)
        if not isinstance(rotation, (int, float)) or not -360 <= rotation <= 360:
            raise SceneValidationError("layer rotation must be between -360 and 360")
        mask = layer.get("mask")
        if mask is not None and not isinstance(mask, dict):
            raise SceneValidationError("layer mask must be an object")

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
                    opacity=int(255 * float(layer.get("opacity", 1.0))),
                )
        return image

    def export(self, path: Path | str, format: str = "PNG") -> Path:
        format = format.upper()
        if format in {"SVG", "PDF"}:
            target = Path(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            if format == "SVG":
                elements = [
                    (
                        f'<svg xmlns="http://www.w3.org/2000/svg" '
                        f'width="{self.width}" height="{self.height}">'
                    ),
                    f'<rect width="100%" height="100%" fill="{self.background}"/>',
                ]
                for layer in self.layers:
                    if layer["type"] == "rectangle":
                        x0, y0, x1, y1 = layer["box"]
                        color = layer.get("fill", "#000000")
                        elements.append(
                            f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" '
                            f'height="{y1 - y0}" fill="{color}"/>'
                        )
                    elif layer["type"] == "ellipse":
                        x0, y0, x1, y1 = layer["box"]
                        color = layer.get("fill", "#000000")
                        elements.append(
                            f'<ellipse cx="{(x0 + x1) / 2}" cy="{(y0 + y1) / 2}" '
                            f'rx="{(x1 - x0) / 2}" ry="{(y1 - y0) / 2}" fill="{color}"/>'
                        )
                    else:
                        x, y = layer.get("xy", [0, 0])
                        color = layer.get("fill", "#000000")
                        size = layer.get("size", 16)
                        elements.append(
                            f'<text x="{x}" y="{y}" fill="{color}" '
                            f'font-size="{size}">{html.escape(layer["text"])}</text>'
                        )
                elements.append("</svg>")
                target.write_text("".join(elements), encoding="utf-8")
            else:
                self.render_image().save(target, format="PDF", resolution=144.0)
            return target
        formats = {"PNG", "JPEG", "WEBP"}
        if format not in formats:
            raise SceneValidationError("supported scene exports are PNG, JPEG, WEBP, SVG, and PDF")
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
