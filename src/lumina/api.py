from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import Response
from PIL import Image

from . import __version__
from .engine import MAX_BYTES, UnsafeOperation, VisualEngine
from .jobs import JobStore
from .models import CreateRequest, EditRequest, ReviseRequest
from .providers import ProviderError


def create_app(output_dir: Path | str | None = None) -> FastAPI:
    root = output_dir or os.getenv("LUMINA_OUTPUT_DIR", "./output")
    engine = VisualEngine(root)
    jobs = JobStore(Path(root) / "jobs.sqlite3")
    app = FastAPI(
        title="Lumina Runtime",
        version=__version__,
        description=(
            "Visual creation, inspection, editing, and revision tools for text-only agents."
        ),
    )

    @app.get("/health")
    def health():
        return {
            "status": "ok",
            "version": __version__,
            "capabilities": [
                "canvas",
                "analysis",
                "safe_edit",
                "revision",
                "compare",
                "artifact-retrieval",
                "durable-jobs",
                "semantic-vision-contract",
                "quality-gates",
                "mcp-adapter",
                "openai-compatible",
            ],
        }

    @app.post("/v1/images", status_code=201)
    def create(request: CreateRequest):
        try:
            return engine.create(
                request.prompt, request.width, request.height, request.provider
            ).artifact_dict()
        except ProviderError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    @app.post("/v1/images/analyze")
    async def analyze(image: Annotated[UploadFile, File()]):
        if not (image.content_type or "").startswith("image/"):
            raise HTTPException(status_code=415, detail="content type must be image/*")
        try:
            data = await image.read(MAX_BYTES + 1)
            return engine.analyze(data).artifact_dict()
        except UnsafeOperation as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/v1/jobs", status_code=202)
    def create_job(request: dict):
        operation = request.get("operation")
        payload = request.get("payload")
        if not isinstance(operation, str):
            raise HTTPException(status_code=422, detail="operation is required")
        if not isinstance(payload, dict):
            payload = {key: value for key, value in request.items() if key != "operation"}
        try:
            return jobs.create(operation, payload)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.get("/v1/jobs/{job_id}")
    def get_job(job_id: str):
        try:
            return jobs.get(job_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="job not found") from exc

    @app.post("/v1/jobs/{job_id}/cancel")
    def cancel_job(job_id: str):
        try:
            return jobs.cancel(job_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="job not found") from exc

    @app.get("/v1/artifacts/{artifact_id}")
    def artifact_metadata(artifact_id: str):
        try:
            path = engine.artifact_path(artifact_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail="artifact not found") from exc
        except UnsafeOperation as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        with Image.open(path) as image:
            width, height = image.size
        return {
            "artifact_id": artifact_id,
            "mime_type": "image/png",
            "width": width,
            "height": height,
            "size_bytes": path.stat().st_size,
        }

    @app.get("/v1/artifacts/{artifact_id}/content")
    def artifact_content(artifact_id: str):
        try:
            data = engine.artifact_bytes(artifact_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail="artifact not found") from exc
        except UnsafeOperation as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return Response(
            content=data,
            media_type="image/png",
            headers={"content-disposition": f'attachment; filename="{artifact_id}.png"'},
        )

    @app.post("/v1/images/compare")
    def compare(request: dict):
        try:
            original = base64.b64decode(request.get("original_base64", ""), validate=True)
            candidate = base64.b64decode(request.get("candidate_base64", ""), validate=True)
        except (ValueError, TypeError) as exc:
            raise HTTPException(status_code=400, detail="images must be valid base64") from exc
        try:
            _, metrics = engine.compare_bytes(original, candidate)
            return metrics
        except UnsafeOperation as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/v1/images/edit")
    def edit(request: EditRequest):
        try:
            data = base64.b64decode(request.image_base64, validate=True)
        except (ValueError, TypeError) as exc:
            raise HTTPException(status_code=400, detail="invalid base64 image") from exc
        try:
            return engine.edit_bytes(data, request.operation, request.params).artifact_dict()
        except UnsafeOperation as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/v1/images/revise")
    def revise(request: ReviseRequest):
        try:
            configured_limit = min(3, max(1, int(os.getenv("LUMINA_MAX_ITERATIONS", "3"))))
        except ValueError:
            configured_limit = 3
        if request.max_iterations > configured_limit:
            raise HTTPException(
                status_code=400,
                detail=f"max_iterations exceeds configured limit of {configured_limit}",
            )
        try:
            data = base64.b64decode(request.image_base64, validate=True)
            source = engine.analyze(data)
        except (ValueError, TypeError) as exc:
            raise HTTPException(status_code=400, detail="invalid base64 image") from exc
        except UnsafeOperation as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return engine.revise(source, request.instruction, request.max_iterations).artifact_dict()

    return app


app = create_app()
