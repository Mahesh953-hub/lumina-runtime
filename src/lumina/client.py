from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import httpx


class LuminaError(RuntimeError):
    pass


class LuminaClient:
    """Small synchronous client for the Lumina HTTP API."""

    def __init__(self, base_url: str = "http://127.0.0.1:8000", timeout: float = 120.0):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(timeout=timeout)

    def close(self) -> None:
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()

    def health(self) -> dict:
        return self._request("GET", "/health")

    def create(
        self, prompt: str, width: int = 512, height: int = 512, provider: str = "canvas"
    ) -> dict:
        return self._request(
            "POST",
            "/v1/images",
            json={"prompt": prompt, "width": width, "height": height, "provider": provider},
        )

    def analyze(self, image_path: str | Path) -> dict:
        with Path(image_path).open("rb") as image:
            return self._request(
                "POST",
                "/v1/images/analyze",
                files={"image": (Path(image_path).name, image, "image/png")},
            )

    def compare(self, original_base64: str, candidate_base64: str) -> dict:
        return self._request(
            "POST",
            "/v1/images/compare",
            json={"original_base64": original_base64, "candidate_base64": candidate_base64},
        )

    def edit(self, image_base64: str, operation: str, params: dict) -> dict:
        return self._request(
            "POST",
            "/v1/images/edit",
            json={"image_base64": image_base64, "operation": operation, "params": params},
        )

    def revise(self, image_base64: str, instruction: str, max_iterations: int = 1) -> dict:
        return self._request(
            "POST",
            "/v1/images/revise",
            json={
                "image_base64": image_base64,
                "instruction": instruction,
                "max_iterations": max_iterations,
            },
        )

    def job(self, operation: str, payload: dict) -> dict:
        return self._request("POST", "/v1/jobs", json={"operation": operation, "payload": payload})

    def get_job(self, job_id: str) -> dict:
        return self._request("GET", f"/v1/jobs/{job_id}")

    def cancel_job(self, job_id: str) -> dict:
        return self._request("POST", f"/v1/jobs/{job_id}/cancel")

    def artifact(self, artifact_id: str) -> dict:
        return self._request("GET", f"/v1/artifacts/{artifact_id}")

    def download(self, artifact_id: str, destination: str | Path) -> Path:
        response = self.client.get(
            urljoin(self.base_url + "/", f"v1/artifacts/{artifact_id}/content")
        )
        if response.status_code >= 400:
            raise LuminaError(f"Lumina request failed: {response.status_code} {response.text}")
        target = Path(destination)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(response.content)
        return target

    def _request(self, method: str, path: str, **kwargs: Any) -> dict:
        response = self.client.request(
            method, urljoin(self.base_url + "/", path.lstrip("/")), **kwargs
        )
        if response.status_code >= 400:
            raise LuminaError(f"Lumina request failed: {response.status_code} {response.text}")
        return response.json()
