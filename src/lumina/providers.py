from __future__ import annotations

import base64
import binascii
import json as json_module
from collections.abc import Callable
from dataclasses import dataclass
from io import BytesIO
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from PIL import Image, ImageOps

MAX_PROVIDER_RESPONSE = 30 * 1024 * 1024
MAX_DECODED_IMAGE = 20 * 1024 * 1024
MAX_PIXELS = 16_000_000


class ProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class ProviderResult:
    image: Image.Image
    width: int
    height: int


class OpenAICompatibleImageProvider:
    def __init__(self, base_url: str, api_key: str, http_post: Callable | None = None):
        if urlparse(base_url).scheme.lower() != "https":
            raise ValueError("IMAGE_BASE_URL must use HTTPS")
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.http_post = http_post or self._post

    def _post(self, url: str, *, json: dict, headers: dict, timeout: int) -> dict:
        request = Request(
            url,
            data=json_module.dumps(json).encode(),
            headers={**headers, "content-type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=timeout) as response:  # nosec B310 - scheme validated as HTTPS
                payload = response.read(MAX_PROVIDER_RESPONSE + 1)
        except (OSError, URLError) as exc:
            raise ProviderError("image provider request failed") from exc
        if len(payload) > MAX_PROVIDER_RESPONSE:
            raise ProviderError("image provider response exceeds 30 MB")
        try:
            return json_module.loads(payload)
        except (UnicodeDecodeError, json_module.JSONDecodeError) as exc:
            raise ProviderError("image provider returned invalid JSON") from exc

    def generate(self, prompt: str, width: int, height: int) -> ProviderResult:
        try:
            response = self.http_post(
                f"{self.base_url}/images/generations",
                json={
                    "model": "gpt-image-1",
                    "prompt": prompt,
                    "size": "1024x1024",
                    "n": 1,
                    "response_format": "b64_json",
                },
                headers={"authorization": f"Bearer {self.api_key}"},
                timeout=120,
            )
        except ProviderError:
            raise
        except Exception as exc:
            raise ProviderError("image provider request failed") from exc
        try:
            encoded = response["data"][0]["b64_json"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError("provider response did not contain valid data[0].b64_json") from exc
        try:
            if not isinstance(encoded, str) or len(encoded) > 28_000_000:
                raise ValueError("encoded provider image exceeds 20 MB")
            raw = base64.b64decode(encoded, validate=True)
            if len(raw) > MAX_DECODED_IMAGE:
                raise ValueError("decoded provider image exceeds 20 MB")
            image = Image.open(BytesIO(raw))
            if image.width * image.height > MAX_PIXELS:
                raise ValueError("provider image dimensions exceed safety limit")
            image.load()
        except ValueError as exc:
            if "20 MB" in str(exc):
                raise ProviderError(str(exc)) from exc
            raise ProviderError("provider image exceeded safety limits") from exc
        except (TypeError, binascii.Error, OSError) as exc:
            raise ProviderError("provider response did not contain a valid bounded image") from exc
        image = ImageOps.fit(image.convert("RGB"), (width, height), method=Image.Resampling.LANCZOS)
        return ProviderResult(image=image, width=width, height=height)
