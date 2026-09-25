from __future__ import annotations

import os
import secrets
from typing import Protocol


class Storage(Protocol):
    def put(self, artifact_id: str, data: bytes) -> None: ...
    def get(self, artifact_id: str) -> bytes: ...
    def delete(self, artifact_id: str) -> None: ...


class LocalStorage:
    def __init__(self, root):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, artifact_id: str):
        if not artifact_id.isalnum() or len(artifact_id) != 32:
            raise ValueError("invalid artifact id")
        return self.root / f"{artifact_id}.bin"

    def put(self, artifact_id, data):
        self._path(artifact_id).write_bytes(data)

    def get(self, artifact_id):
        try:
            return self._path(artifact_id).read_bytes()
        except FileNotFoundError as exc:
            raise KeyError(artifact_id) from exc

    def delete(self, artifact_id):
        self._path(artifact_id).unlink(missing_ok=True)


def configured_api_key() -> str | None:
    return os.getenv("LUMINA_API_KEY") or None


def valid_api_key(candidate: str | None) -> bool:
    expected = configured_api_key()
    return expected is None or (
        candidate is not None and secrets.compare_digest(candidate, expected)
    )
