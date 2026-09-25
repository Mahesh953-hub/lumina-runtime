"""Small MCP-style adapter for the canonical Lumina HTTP API.

The adapter deliberately contains no image implementation. It translates MCP
method calls to Lumina's documented HTTP routes so deployments can use either
transport without changing visual behavior.
"""

from __future__ import annotations

import base64
from typing import Any

import httpx


class LuminaMCPAdapter:
    def __init__(self, base_url: str = "http://127.0.0.1:8000", timeout: float = 120.0):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(timeout=timeout)

    def close(self) -> None:
        self.client.close()

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict:
        routes = {
            "create_image": ("POST", "/v1/images"),
            "analyze_image": ("POST", "/v1/images/analyze"),
            "compare_images": ("POST", "/v1/images/compare"),
            "edit_image": ("POST", "/v1/images/edit"),
            "revise_image": ("POST", "/v1/images/revise"),
        }
        if name == "get_artifact":
            response = self.client.get(f"{self.base_url}/v1/artifacts/{arguments['artifact_id']}")
        elif name in routes:
            method, path = routes[name]
            response = self.client.request(method, f"{self.base_url}{path}", json=arguments)
        else:
            raise ValueError(f"unknown MCP tool: {name}")
        response.raise_for_status()
        return response.json()

    def encode_image(self, image: bytes) -> str:
        return base64.b64encode(image).decode()
