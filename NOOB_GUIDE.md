# Lumina: beginner guide

## What is Lumina?

Lumina is a runtime that gives an AI agent visual tools. The agent may only understand text, but it can ask Lumina to create an image, inspect the image, edit it, compare two images, and revise it.

Lumina does not give the language model visual neurons. It gives the agent a safe tool boundary and returns structured information about the result.

```text
Agent: create an image, check it, and fix it
             |
             v
          Lumina API
             |
      create -> observe -> revise
```

## Requirements

- Python 3.11 or newer
- About 300 MB of disk space for the virtual environment and dependencies
- Optional: an HTTPS image-generation provider for realistic AI images

You do not need a GPU to run the local canvas and analysis tools.

## Install

```bash
git clone https://github.com/Mahesh953-hub/lumina-runtime.git
cd lumina-runtime
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .
```

For development tools, install the extra dependencies:

```bash
python -m pip install -e '.[dev]'
```

Windows PowerShell activation is:

```powershell
.venv\Scripts\Activate.ps1
```

## Start the server

```bash
lumina serve
```

The default address is <http://127.0.0.1:8000>.

The interactive API documentation is at <http://127.0.0.1:8000/docs>. It lists every request field and shows example responses.

Check that the server is alive:

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{
  "status": "ok",
  "version": "0.1.0",
  "capabilities": ["canvas", "analysis", "safe_edit", "revision", "openai-compatible"]
}
```

## Create an image

The local `canvas` backend is deterministic. It is useful for shapes, colors, layout experiments, and learning the API. It is not a realistic diffusion model.

```bash
curl -X POST http://127.0.0.1:8000/v1/images \
  -H 'content-type: application/json' \
  -d '{
    "prompt": "a red circle on white",
    "width": 256,
    "height": 256,
    "provider": "canvas"
  }'
```

The response includes:

- `artifact_id`: an opaque identifier for the stored image
- `image_base64`: the PNG encoded as text
- `width` and `height`: actual image dimensions
- `revision`: the edit generation number
- `observation`: machine-readable colors, geometry, and quality measurements

Base64 is convenient for an agent because one JSON response contains both the artifact identifier and the pixels. For a browser, prefer an endpoint that streams the artifact as an image once artifact retrieval is available.

## Analyze an image

```bash
curl -X POST http://127.0.0.1:8000/v1/images/analyze \
  -F image=@my-image.png
```

Analysis reports:

- dominant colors and their fractions
- mean RGB
- estimated background color
- content bounding box
- non-background fraction
- brightness, contrast, entropy, and dynamic range

These are pixel measurements. They do not mean that Lumina understands whether a person is smiling or whether a generated object matches a prompt. Semantic understanding requires a future vision provider.

## Edit an image

The editing API uses a JSON object with an image, an allow-listed operation, and operation parameters.

```bash
curl -X POST http://127.0.0.1:8000/v1/images/edit \
  -H 'content-type: application/json' \
  -d '{
    "image_base64": "PASTE_BASE64_IMAGE",
    "operation": "draw_text",
    "params": {
      "text": "Lumina",
      "xy": [20, 20],
      "size": 32,
      "fill": "#111111"
    }
  }'
```

Allowed operations:

- `draw_rectangle`
- `draw_ellipse`
- `draw_text`
- `blur`
- `sharpen`
- `brighten`
- `contrast`

Lumina rejects unknown operations. It does not execute agent-provided Python, shell commands, URLs, or paths.

## Revise an image

```bash
curl -X POST http://127.0.0.1:8000/v1/images/revise \
  -H 'content-type: application/json' \
  -d '{
    "image_base64": "PASTE_BASE64_IMAGE",
    "instruction": "increase contrast",
    "max_iterations": 1
  }'
```

The current revision loop understands deterministic instructions such as contrast, brightness, and sharpness. More meaningful revisions require a vision model and a visual planner in later phases.

## Long-running jobs

Queue an asynchronous visual job:

```bash
curl -X POST http://127.0.0.1:8000/v1/jobs \
  -H 'content-type: application/json' \
  -d '{"operation":"create","payload":{"prompt":"a red circle","width":256,"height":256}}'
```

Read its state and replayable events with `GET /v1/jobs/{job_id}`. Cancel a job with `POST /v1/jobs/{job_id}/cancel`. Run a separate worker with `lumina-worker --output-dir ./output`; it processes one job at a time and recovers interrupted running jobs on startup. Use `lumina-worker --once` in a test or controlled batch process.

Semantic providers implement the `SemanticVisionProvider` contract and return `SemanticObservation` values containing captions, objects, relationships, OCR text, and required-element coverage. `quality_gate()` turns that feedback into a pass/fail decision. Lumina does not pretend that its pixel observations are semantic understanding.

## Compare and retrieve artifacts

Compare two same-sized images:

```bash
curl -X POST http://127.0.0.1:8000/v1/images/compare \
  -H 'content-type: application/json' \
  -d '{"original_base64":"...","candidate_base64":"..."}'
```

The response includes `mismatch_fraction`, `mean_absolute_error`, `rms_error`, and a `difference_artifact_id`. Retrieve metadata or download the stored PNG with `/v1/artifacts/{artifact_id}` and `/v1/artifacts/{artifact_id}/content`.

Use the SDK:

```python
from lumina.client import LuminaClient

with LuminaClient() as lumina:
    result = lumina.create("a red circle", 256, 256)
    lumina.download(result["artifact_id"], "circle.png")
```

## Use an external image provider

For realistic generated images, configure an OpenAI-compatible image endpoint:

```bash
export IMAGE_BASE_URL=https://your-provider.example/v1
export IMAGE_API_KEY=replace-with-a-real-key
lumina serve
```

Then submit:

```json
{
  "prompt": "a library at sunset",
  "width": 1024,
  "height": 1024,
  "provider": "openai-compatible"
}
```

Lumina requires HTTPS for provider URLs, limits the response size, checks the image dimensions, and normalizes the returned image to the requested dimensions. The provider key stays on the Lumina server.

## How the pieces fit together

```text
Your agent
   |
   | JSON request
   v
FastAPI boundary
   |
   v
VisualEngine
   |---- Pillow and NumPy local tools
   |---- OpenAI-compatible external provider
   v
Observation contract
   |
   +---- color, geometry, quality, revisions
```

Lumina uses precise deterministic tools for shapes and text. Neural providers are better for realistic imagery. A future scene graph will combine both approaches into editable visual compositions.

## Common beginner problems

### `ModuleNotFoundError: lumina`

The virtual environment is active but the package is not installed. Run:

```bash
python -m pip install -e .
```

### `Address already in use`

Choose another port:

```bash
lumina serve --port 8001
```

Then replace `8000` with `8001` in the examples.

### The external provider returns an error

Check that:

- `IMAGE_BASE_URL` begins with `https://`
- the URL points to the API base, not the full generations path
- the provider supports `/v1/images/generations`
- the response contains `data[0].b64_json`
- the API key is valid and has not expired

### A realistic image looks flat or simple

The local canvas only creates simple deterministic graphics. Use a configured neural provider for realism.

### The server says the image is too large

Lumina limits upload bytes, decoded dimensions, provider responses, and pixels for safety. Resize the image or change the requested dimensions.

## What is not finished yet

See [PLAN.md](PLAN.md) for the phased backlog. The next practical phase adds image comparison, artifact retrieval, and a Python client. Later phases add durable asynchronous jobs, semantic vision, MCP, editable scene graphs, and production security/storage.

## Development commands

```bash
pytest -q
ruff check .
bandit -q -r src
```

Run those commands before committing a change. A checkbox in the roadmap should be changed only when the corresponding behavior and tests exist.
