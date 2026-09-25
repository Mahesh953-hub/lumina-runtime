from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, HTTPException, UploadFile

from . import __version__
from .engine import MAX_BYTES, UnsafeOperation, VisualEngine
from .models import CreateRequest, EditRequest, ReviseRequest
from .providers import ProviderError


def create_app(output_dir: Path | str | None = None) -> FastAPI:
    root = output_dir or os.getenv("LUMINA_OUTPUT_DIR", "./output")
    engine = VisualEngine(root)
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
            "capabilities": ["canvas", "analysis", "safe_edit", "revision", "openai-compatible"],
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
