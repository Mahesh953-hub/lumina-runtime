from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from datetime import UTC, datetime
from pathlib import Path

from .engine import VisualEngine

OPERATIONS = {"create", "analyze", "compare", "edit", "revise"}


def _now() -> str:
    return datetime.now(UTC).isoformat()


class JobStore:
    def __init__(self, path: Path | str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        with self._lock, self._connect() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, operation TEXT NOT NULL, "
                "payload TEXT NOT NULL, state TEXT NOT NULL, result TEXT, events TEXT NOT NULL, "
                "created_at TEXT NOT NULL, updated_at TEXT NOT NULL)"
            )
        self.recover_interrupted()

    def _connect(self):
        db = sqlite3.connect(self.path, timeout=30)
        db.execute("PRAGMA busy_timeout=30000")
        return db

    def create(self, operation: str, payload: dict) -> dict:
        if operation not in OPERATIONS:
            raise ValueError("unsupported job operation")
        job_id = uuid.uuid4().hex
        now = _now()
        record = {
            "job_id": job_id,
            "operation": operation,
            "payload": payload,
            "state": "queued",
            "result": None,
            "created_at": now,
            "updated_at": now,
            "events": [{"event": "job.queued", "at": now}],
        }
        with self._lock, self._connect() as db:
            db.execute(
                "INSERT INTO jobs "
                "(id, operation, payload, state, result, events, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    job_id,
                    operation,
                    json.dumps(payload),
                    "queued",
                    None,
                    json.dumps(record["events"]),
                    now,
                    now,
                ),
            )
        return record

    def get(self, job_id: str) -> dict:
        with self._connect() as db:
            row = db.execute(
                "SELECT id, operation, payload, state, result, events, created_at, updated_at "
                "FROM jobs WHERE id = ?",
                (job_id,),
            ).fetchone()
        if not row:
            raise KeyError(job_id)
        return {
            "job_id": row[0],
            "operation": row[1],
            "payload": json.loads(row[2]),
            "state": row[3],
            "result": json.loads(row[4]) if row[4] else None,
            "events": json.loads(row[5]),
            "created_at": row[6],
            "updated_at": row[7],
        }

    def recover_interrupted(self) -> int:
        with self._lock, self._connect() as db:
            rows = db.execute("SELECT id, events FROM jobs WHERE state = 'running'").fetchall()
            now = _now()
            for job_id, events_json in rows:
                events = json.loads(events_json)
                events.append({"event": "job.requeued", "at": now})
                db.execute(
                    "UPDATE jobs SET state = 'queued', events = ? WHERE id = ?",
                    (json.dumps(events), job_id),
                )
        return len(rows)

    def next_queued(self) -> dict | None:
        with self._lock, self._connect() as db:
            row = db.execute(
                "SELECT id FROM jobs WHERE state = 'queued' ORDER BY rowid LIMIT 1"
            ).fetchone()
        return self.get(row[0]) if row else None

    def update(self, job_id: str, state: str, result: dict | None = None, event: str | None = None):
        current = self.get(job_id)
        current["state"] = state
        current["result"] = result
        current["updated_at"] = _now()
        if event:
            current["events"].append({"event": event, "at": current["updated_at"]})
        with self._lock, self._connect() as db:
            db.execute(
                "UPDATE jobs SET state = ?, result = ?, events = ?, updated_at = ? WHERE id = ?",
                (
                    state,
                    json.dumps(result) if result is not None else None,
                    json.dumps(current["events"]),
                    current["updated_at"],
                    job_id,
                ),
            )
        return current

    def cancel(self, job_id: str) -> dict:
        current = self.get(job_id)
        if current["state"] in {"completed", "failed", "canceled"}:
            return current
        return self.update(job_id, "canceled", event="job.canceled")


class VisualJobWorker:
    def __init__(self, store: JobStore, output_dir: Path | str = "output"):
        self.store = store
        self.engine = VisualEngine(output_dir)

    def run_once(self) -> dict | None:
        job = self.store.next_queued()
        if not job:
            return None
        self.store.update(job["job_id"], "running", event="job.running")
        try:
            result = self._execute(job)
        except Exception as exc:
            return self.store.update(job["job_id"], "failed", {"error": str(exc)}, "job.failed")
        return self.store.update(job["job_id"], "completed", result, "job.completed")

    def _execute(self, job: dict) -> dict:
        payload = job["payload"]
        operation = job["operation"]
        if operation == "create":
            return self.engine.create(
                payload["prompt"],
                int(payload.get("width", 512)),
                int(payload.get("height", 512)),
                payload.get("provider", "canvas"),
            ).artifact_dict()
        if operation == "analyze":
            import base64

            return self.engine.analyze(
                base64.b64decode(payload["image_base64"], validate=True)
            ).artifact_dict()
        if operation == "compare":
            import base64

            _, result = self.engine.compare_bytes(
                base64.b64decode(payload["original_base64"], validate=True),
                base64.b64decode(payload["candidate_base64"], validate=True),
            )
            return result
        if operation == "edit":
            import base64

            return self.engine.edit_bytes(
                base64.b64decode(payload["image_base64"], validate=True),
                payload["edit_operation"],
                payload.get("params", {}),
            ).artifact_dict()
        if operation == "revise":
            import base64

            source = self.engine.analyze(base64.b64decode(payload["image_base64"], validate=True))
            return self.engine.revise(
                source,
                payload["instruction"],
                min(3, int(payload.get("max_iterations", 1))),
            ).artifact_dict()
        raise ValueError(f"worker operation not implemented: {operation}")
