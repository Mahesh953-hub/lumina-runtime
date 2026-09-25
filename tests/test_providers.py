import base64
from io import BytesIO
from urllib.error import URLError

import pytest
from PIL import Image

from lumina.providers import OpenAICompatibleImageProvider, ProviderError


def encoded_image(size=(8, 8)):
    buffer = BytesIO()
    Image.new("RGB", size, (255, 0, 0)).save(buffer, "PNG")
    return base64.b64encode(buffer.getvalue()).decode()


def test_openai_compatible_provider_builds_request_and_normalizes_dimensions():
    captured = {}

    def fake_post(url, *, json, headers, timeout):
        captured.update(url=url, json=json, headers=headers, timeout=timeout)
        return {"data": [{"b64_json": encoded_image()}]}

    provider = OpenAICompatibleImageProvider(
        base_url="https://example.test/v1", api_key="secret", http_post=fake_post
    )
    result = provider.generate("a red image", 16, 8)
    assert result.image.size == (16, 8)
    assert result.width == 16
    assert captured["url"] == "https://example.test/v1/images/generations"
    assert captured["json"]["size"] == "1024x1024"


def test_provider_rejects_invalid_response():
    provider = OpenAICompatibleImageProvider(
        base_url="https://example.test/v1", api_key="secret", http_post=lambda *a, **k: {}
    )
    with pytest.raises(ProviderError, match="b64_json"):
        provider.generate("x", 8, 8)


def test_provider_converts_transport_error():
    def fail(*args, **kwargs):
        raise URLError("private network details")

    provider = OpenAICompatibleImageProvider(
        base_url="https://example.test/v1", api_key="secret", http_post=fail
    )
    with pytest.raises(ProviderError, match="request failed"):
        provider.generate("x", 8, 8)


def test_provider_rejects_oversized_decoded_image():
    encoded = "A" * 29_000_000
    provider = OpenAICompatibleImageProvider(
        base_url="https://example.test/v1",
        api_key="secret",
        http_post=lambda *a, **k: {"data": [{"b64_json": encoded}]},
    )
    with pytest.raises(ProviderError, match="20 MB"):
        provider.generate("x", 8, 8)


def test_provider_rejects_non_https_url():
    with pytest.raises(ValueError, match="HTTPS"):
        OpenAICompatibleImageProvider("http://example.test/v1", "secret")
