# Lumina Runtime

A multimodal runtime that gives text-only agents controlled tools to create, inspect, edit, and iterate on images.

Lumina is not a new model. It is the visual execution layer between an agent and image backends. The deterministic canvas works locally with Pillow and NumPy; external diffusion-compatible endpoints can be added through providers.

## What works now

- Create PNG images with a local deterministic canvas
- Analyze geometry, color, brightness, contrast, and entropy
- Edit images with safe drawing and filter operations
- Revise images through a feedback-driven contrast operation
- Invoke OpenAI-compatible image generation endpoints
- FastAPI and JSON HTTP API with OpenAPI documentation
- Bounded dimensions, decoded-image validation, and opaque artifact IDs
- Tests, Docker image, CLI, and CI configuration

## Documentation

New users should read [NOOB_GUIDE.md](NOOB_GUIDE.md) for installation, concepts, API examples, and troubleshooting. The implementation backlog and acceptance criteria live in [PLAN.md](PLAN.md).

## Quick start

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
lumina serve
```

Open <http://127.0.0.1:8000/docs> and create an image:

```bash
curl -s http://127.0.0.1:8000/v1/images \
  -H 'content-type: application/json' \
  -d '{"prompt":"a red circle on white","width":512,"height":512,"provider":"canvas"}'
```

Analyze an image:

```bash
curl -s http://127.0.0.1:8000/v1/images/analyze \
  -F image=@example.png
```

## External image generation

Lumina supports OpenAI-compatible `/v1/images/generations` responses containing `data[0].b64_json`.

```bash
export IMAGE_API_KEY=...
export IMAGE_BASE_URL=https://your-provider.example/v1
lumina serve
```

Then submit `"provider": "openai-compatible"`. Provider responses are copied to local artifact storage; clients never need filesystem paths.

## Agent operations

| Operation | Purpose |
|---|---|
| `create_image` | Render a new image through a selected backend |
| `analyze_image` | Return machine-readable visual observations |
| `edit_image` | Apply one allow-listed editing operation |
| `revise_image` | Run a bounded visual feedback iteration |
| `compare_images` | Return mismatch metrics and a difference artifact |
| `create_job` | Queue a durable visual job |
| `get_job` | Read job state, result, and replayable events |
| `cancel_job` | Cancel a queued or running job |
| `get_artifact` | Retrieve metadata or download a stored artifact |

`LuminaMCPAdapter` in `lumina.mcp` maps MCP-style tool names to the canonical HTTP API. `SemanticObservation` and `quality_gate` in `lumina.vision` define the semantic feedback contract for future vision providers.

Supported edit operations include `draw_rectangle`, `draw_ellipse`, `draw_text`, `blur`, `sharpen`, `brighten`, and `contrast`. The API rejects unknown operations instead of executing arbitrary code or shell commands.

## Architecture

```text
Text-only agent
      |
      | JSON over HTTP
      v
FastAPI tool boundary
      |
      v
VisualEngine ---- observation / quality feedback
   |       |
   |       +-- revision loop
   |
   +-- Pillow + NumPy canvas
   +-- OpenCV backend (optional)
   +-- OpenAI-compatible diffusion provider
```

The runtime intentionally combines deterministic and neural tools. Shapes, labels, and layouts use precise tools; open-ended generation uses a configured neural backend; every result can be inspected again.

## Configuration

| Variable | Default | Meaning |
|---|---:|---|
| `LUMINA_OUTPUT_DIR` | `./output` | Local artifact directory |
| `IMAGE_BASE_URL` | unset | OpenAI-compatible base URL |
| `IMAGE_API_KEY` | unset | Provider API key |
| `LUMINA_MAX_ITERATIONS` | `3` | Maximum revision iterations accepted by the API |
| `LUMINA_MAX_ARTIFACTS` | `1000` | Maximum retained local PNG artifacts (1–10,000) |
| `LUMINA_HOST` | `127.0.0.1` | Bind address |
| `LUMINA_PORT` | `8000` | Bind port |

## Development

```bash
pip install -e '.[dev]'
pytest -q
ruff check .
```

## Deployment

```bash
docker build -t lumina-runtime .
docker run --rm -p 8000:8000 -v "$PWD/output:/data/output" lumina-runtime
```

## Security and limitations

This runtime is a tool service, not an operating-system sandbox for arbitrary Python. Agents submit declarative operations, not code. Image dimensions and byte size are bounded, and artifacts use generated IDs.

The local canvas is intentionally deterministic and illustrative; it is not a diffusion model. Production image generation requires a configured provider or an extension implementing the provider interface. Semantic vision-model analysis can be added behind the same observation contract.

## License

MIT
