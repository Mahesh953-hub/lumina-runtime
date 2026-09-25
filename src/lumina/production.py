from __future__ import annotations

import os
import secrets
from typing import Protocol


class Storage(Protocol):
    def put(self, artifact_id: str, data: bytes) -> None: ...
    def get(self, artifact_id: str) -> bytes: ...
    def delete(self, artifact_id: str) -> None: ...


def _safe_id(artifact_id: str) -> str:
    if len(artifact_id) != 32 or any(c not in "0123456789abcdef" for c in artifact_id):
        raise ValueError("invalid artifact id")
    return artifact_id


class LocalStorage:
    def __init__(self, root):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def path(self, artifact_id: str):
        return self.root / f"{_safe_id(artifact_id)}.bin"

    def put(self, artifact_id: str, data: bytes):
        self.path(artifact_id).write_bytes(data)

    def get(self, artifact_id: str) -> bytes:
        return self.path(artifact_id).read_bytes()

    def delete(self, artifact_id: str):
        self.path(artifact_id).unlink(missing_ok=True)


class S3Storage:
    def __init__(self, bucket: str, prefix: str = "artifacts", client=None):
        if client is None:
            try:
                import boto3
            except ImportError as exc:
                raise RuntimeError("install boto3 for S3 storage") from exc
            client = boto3.client("s3")
        self.bucket, self.prefix, self.client = bucket, prefix.strip("/"), client

    def _key(self, artifact_id: str) -> str:
        return f"{self.prefix}/{_safe_id(artifact_id)}.bin"

    def put(self, artifact_id: str, data: bytes):
        self.client.put_object(Bucket=self.bucket, Key=self._key(artifact_id), Body=data)

    def get(self, artifact_id: str) -> bytes:
        body = self.client.get_object(Bucket=self.bucket, Key=self._key(artifact_id))["Body"]
        return body if isinstance(body, bytes) else body.read()

    def delete(self, artifact_id: str):
        self.client.delete_object(Bucket=self.bucket, Key=self._key(artifact_id))


class MetadataStore(Protocol):
    def put(self, artifact_id: str, metadata: dict) -> None: ...
    def get(self, artifact_id: str) -> dict: ...
    def list_tenant(self, tenant_id: str) -> list[dict]: ...


class MemoryMetadataStore:
    def __init__(self):
        self.records: dict[str, dict] = {}

    def put(self, artifact_id: str, metadata: dict):
        self.records[_safe_id(artifact_id)] = dict(metadata)

    def get(self, artifact_id: str) -> dict:
        return dict(self.records[_safe_id(artifact_id)])

    def list_tenant(self, tenant_id: str) -> list[dict]:
        return [
            dict(v)
            for v in self.records.values()
            if v.get("tenant_id") == tenant_id or v.get("tenant") == tenant_id
        ]


class PostgresMetadataStore:
    def __init__(self, dsn: str | None = None, connection=None):
        if connection is None:
            try:
                import psycopg
            except ImportError as exc:
                raise RuntimeError("install psycopg for PostgreSQL metadata") from exc
            connection = psycopg.connect(dsn or os.environ["DATABASE_URL"])
        self.connection = connection

    def put(self, artifact_id: str, metadata: dict):
        import json

        with self.connection.cursor() as cur:
            cur.execute(
                (
                    "INSERT INTO artifacts (id, metadata) VALUES (%s, %s) "
                    "ON CONFLICT (id) DO UPDATE SET metadata = EXCLUDED.metadata"
                ),
                (_safe_id(artifact_id), json.dumps(metadata)),
            )
            self.connection.commit()

    def get(self, artifact_id: str) -> dict:
        import json

        with self.connection.cursor() as cur:
            cur.execute("SELECT metadata FROM artifacts WHERE id = %s", (_safe_id(artifact_id),))
            row = cur.fetchone()
        return json.loads(row[0]) if row else {}

    def list_tenant(self, tenant_id: str) -> list[dict]:
        import json

        with self.connection.cursor() as cur:
            cur.execute(
                "SELECT metadata FROM artifacts WHERE metadata->>'tenant_id' = %s", (tenant_id,)
            )
            return [json.loads(row[0]) for row in cur.fetchall()]


class TenantPolicy:
    def __init__(self, max_cost: float = 100.0, max_requests: int = 10_000):
        if max_cost < 0 or max_requests < 1:
            raise ValueError("invalid tenant policy")
        self.max_cost, self.max_requests = max_cost, max_requests

    def allow(self, tenant: str, current_cost: float, current_requests: int) -> bool:
        return (
            bool(tenant) and current_cost < self.max_cost and current_requests < self.max_requests
        )


def configured_api_key() -> str | None:
    return os.getenv("LUMINA_API_KEY") or None


def valid_api_key(candidate: str | None) -> bool:
    expected = configured_api_key()
    return expected is None or (
        candidate is not None and secrets.compare_digest(candidate, expected)
    )
