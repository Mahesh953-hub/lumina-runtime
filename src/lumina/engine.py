from __future__ import annotations

import base64
import io
import os
import uuid
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw, ImageEnhance, ImageFilter, ImageFont

from .observations import observe
from .providers import OpenAICompatibleImageProvider, ProviderError

MAX_BYTES = 15 * 1024 * 1024
ALLOWED_OPERATIONS = {
    "draw_rectangle",
    "draw_ellipse",
    "draw_text",
    "blur",
    "sharpen",
    "brighten",
    "contrast",
}


class UnsafeOperation(ValueError):
    pass


@dataclass(frozen=True)
class VisualResult:
    artifact_id: str
    image_base64: str
    mime_type: str
    width: int
    height: int
    provider: str
    operation: str
    revision: int
    observation: dict

    def artifact_dict(self) -> dict:
        return self.__dict__.copy()


class VisualEngine:
    def __init__(self, output_dir: Path | str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        base_url = os.getenv("IMAGE_BASE_URL")
        api_key = os.getenv("IMAGE_API_KEY")
        self.external = (
            OpenAICompatibleImageProvider(base_url, api_key) if base_url and api_key else None
        )

    def create(
        self, prompt: str, width: int, height: int, provider: str = "canvas"
    ) -> VisualResult:
        if provider == "openai-compatible":
            if not self.external:
                raise ProviderError("IMAGE_BASE_URL and IMAGE_API_KEY are required")
            image = self.external.generate(prompt, width, height).image
        else:
            image = self._canvas(prompt, width, height)
        return self._persist(image, provider, "create", 1)

    def analyze(self, data: bytes) -> VisualResult:
        image = self._decode(data)
        return self._persist(image, "local", "analyze", 1)

    def edit_bytes(
        self, data: bytes, operation: str, params: dict, revision: int = 2
    ) -> VisualResult:
        image = self._decode(data)
        if operation not in ALLOWED_OPERATIONS:
            raise UnsafeOperation(f"unsupported operation: {operation}")
        image = self._apply(image, operation, params)
        return self._persist(image, "local", operation, revision)

    def edit(self, result: VisualResult, operation: str, params: dict) -> VisualResult:
        return self.edit_bytes(
            base64.b64decode(result.image_base64), operation, params, result.revision + 1
        )

    def revise(
        self, result: VisualResult, instruction: str, max_iterations: int = 1
    ) -> VisualResult:
        instruction_l = instruction.lower()
        if "contrast" in instruction_l:
            operation = "contrast"
            params = {"factor": 1.5}
        elif "bright" in instruction_l:
            operation = "brighten"
            params = {"factor": 1.3}
        elif "sharp" in instruction_l:
            operation = "sharpen"
            params = {"factor": 2.0}
        else:
            operation = "contrast"
            params = {"factor": 1.2}
        data = base64.b64decode(result.image_base64)
        current = result
        for iteration in range(max_iterations):
            current = self.edit_bytes(data, operation, params, result.revision + iteration + 1)
            data = base64.b64decode(current.image_base64)
        return current

    def _canvas(self, prompt: str, width: int, height: int) -> Image.Image:
        lowered = prompt.lower()
        if any(word in lowered for word in ("black", "dark", "night")):
            base, foreground = "#111827", "#f9fafb"
        elif any(word in lowered for word in ("red", "crimson")):
            base, foreground = "#fff7ed", "#dc2626"
        else:
            base, foreground = "#f8fafc", "#2563eb"
        image = Image.new("RGB", (width, height), base)
        draw = ImageDraw.Draw(image)
        margin = max(2, min(width, height) // 12)
        box = [margin, margin, width - margin - 1, height - margin - 1]
        if "circle" in lowered or "ellipse" in lowered:
            draw.ellipse(box, fill=foreground)
        elif "line" in lowered:
            draw.line(
                [margin, margin, width - margin, height - margin],
                fill=foreground,
                width=max(2, margin // 3),
            )
        else:
            draw.rectangle(box, fill=foreground)
        # deterministic color bar gives agents useful visual structure
        for index, color in enumerate(("#ef4444", "#f59e0b", "#22c55e", "#3b82f6")):
            x0 = width * index // 4
            x1 = width * (index + 1) // 4
            draw.rectangle([x0, height - max(4, height // 25), x1, height], fill=color)
        return image

    def _decode(self, data: bytes) -> Image.Image:
        if not data or len(data) > MAX_BYTES:
            raise UnsafeOperation("image is empty or exceeds 15 MB")
        try:
            image = Image.open(io.BytesIO(data))
            if image.width * image.height > 16_000_000:
                raise UnsafeOperation("image dimensions exceed safety limit")
            image.load()
        except UnsafeOperation:
            raise
        except (OSError, ValueError) as exc:
            raise UnsafeOperation("input is not a decodable image") from exc
        return image.convert("RGB")

    def _apply(self, image: Image.Image, operation: str, params: dict) -> Image.Image:
        if operation in {"draw_rectangle", "draw_ellipse"}:
            box = self._box(params.get("box"), image)
            fill = self._color(params.get("fill", "#ffffff"))
            draw = ImageDraw.Draw(image)
            if operation == "draw_rectangle":
                draw.rectangle(box, fill=fill)
            else:
                draw.ellipse(box, fill=fill)
            return image
        if operation == "draw_text":
            xy = params.get("xy", [0, 0])
            if not isinstance(xy, list) or len(xy) != 2 or not all(isinstance(v, int) for v in xy):
                raise UnsafeOperation("xy must be [x, y]")
            text = str(params.get("text", ""))[:200]
            if not text or any(ord(char) < 32 for char in text):
                raise UnsafeOperation("text contains invalid characters")
            size = min(200, max(8, int(params.get("size", image.height // 5))))
            font = ImageFont.load_default(size=size)
            ImageDraw.Draw(image).text(
                tuple(xy), text, fill=self._color(params.get("fill", "#000000")), font=font
            )
            return image
        factor = min(5.0, max(-5.0, float(params.get("factor", 1.0))))
        if operation == "blur":
            return image.filter(ImageFilter.GaussianBlur(radius=abs(factor)))
        if operation == "sharpen":
            return ImageEnhance.Sharpness(image).enhance(1 + abs(factor))
        if operation == "brighten":
            return ImageEnhance.Brightness(image).enhance(1 + factor)
        return ImageEnhance.Contrast(image).enhance(1 + abs(factor))

    @staticmethod
    def _box(value, image: Image.Image):
        if (
            not isinstance(value, list)
            or len(value) != 4
            or not all(isinstance(v, int) for v in value)
        ):
            raise UnsafeOperation("box must be [x0, y0, x1, y1]")
        x0, y0, x1, y1 = value
        if not (0 <= x0 < x1 <= image.width and 0 <= y0 < y1 <= image.height):
            raise UnsafeOperation("box must be within image bounds")
        return value

    @staticmethod
    def _color(value) -> str | tuple[int, int, int]:
        try:
            if isinstance(value, list):
                if len(value) != 3 or not all(isinstance(v, int) and 0 <= v <= 255 for v in value):
                    raise ValueError
                return tuple(value)
            return ImageColor.getrgb(value) and value if not isinstance(value, str) else value
        except (TypeError, ValueError) as exc:
            raise UnsafeOperation("invalid color") from exc

    def _enforce_retention(self) -> None:
        try:
            limit = min(10_000, max(1, int(os.getenv("LUMINA_MAX_ARTIFACTS", "1000"))))
        except ValueError:
            limit = 1000
        artifacts = sorted(self.output_dir.glob("*.png"), key=lambda path: path.stat().st_mtime)
        for path in artifacts[max(0, limit - 1) :]:
            path.unlink(missing_ok=True)

    def _persist(
        self, image: Image.Image, provider: str, operation: str, revision: int
    ) -> VisualResult:
        image = image.convert("RGB")
        artifact_id = uuid.uuid4().hex
        self._enforce_retention()
        path = self.output_dir / f"{artifact_id}.png"
        image.save(path, "PNG", optimize=True)
        buffer = io.BytesIO()
        image.save(buffer, "PNG", optimize=True)
        return VisualResult(
            artifact_id=artifact_id,
            image_base64=base64.b64encode(buffer.getvalue()).decode(),
            mime_type="image/png",
            width=image.width,
            height=image.height,
            provider=provider,
            operation=operation,
            revision=revision,
            observation=observe(image),
        )
