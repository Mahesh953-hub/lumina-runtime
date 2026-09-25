# Lumina Runtime v0.1.0 — neutral release test report

## Scope

This is a black-box, local execution test of the released `lumina-runtime` package. It does not claim to be a semantic or subjective image-quality benchmark. The default backend used here is Lumina's deterministic `canvas` provider because no external image-generation credentials were supplied.

The test exercised the public FastAPI application through `TestClient`, using eight increasingly complex prompts. Each prompt was tested through:

1. image creation
2. deterministic declarative text editing
3. image analysis
4. original/edited image comparison
5. scene composition and artifact retrieval

## Results

| Check | Result |
|---|---:|
| Prompts | 8 |
| Create successes | 8/8 |
| Edit successes | 8/8 |
| Analyze successes | 8/8 |
| Compare successes | 8/8 |
| Scene render successes | 8/8 |
| Health check | HTTP 200 |
| Runtime issues detected | 0 |

The complete request/response records are in `responses.json`. The machine-readable result is in `summary.json`.

## Evidence

- `images/prompt-01-create.png` through `images/prompt-08-create.png`
- `images/prompt-01-edit.png` through `images/prompt-08-edit.png`
- `canvases/scene-01.png` through `canvases/scene-08.png`
- `responses.json`
- `summary.json`
- `run_release_tests.py`

All PNGs were opened after generation and checked for valid dimensions and non-zero file size.

## Findings

No execution errors or HTTP failures were found in the tested scope.

The eight scene canvases are intentionally identical because the same scene document is rendered eight times. This tests deterministic reproducibility, not creative variation.

The prompt images are also deterministic canvas outputs. The test verifies transport, persistence, editing, analysis, comparison, scene rendering, and artifact retrieval. It does not evaluate whether an external diffusion model would satisfy the prose prompts.

## Local database

The runtime uses SQLite at:

```text
<output-dir>/jobs.sqlite3
```

No Docker or external database service is required. The release test created the database inside a temporary local directory, confirmed the SQLite schema, and recorded the result in `responses.json`. For normal local use:

```bash
LUMINA_OUTPUT_DIR=./output .venv/bin/lumina serve
```

Jobs are then stored in `./output/jobs.sqlite3`.

## Reproduce

From the repository root:

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/python tests/0.1.0/run_release_tests.py
.venv/bin/ruff check .
.venv/bin/pytest -q
bandit -q -r src
```

## Not tested

- Real semantic vision model integration, intentionally excluded from v0.1.0
- External image-generation provider credentials and billing
- Distributed PostgreSQL deployment
- Distributed S3 deployment
- Multi-process locking
- Long-duration load testing
- Visual quality against human aesthetic preferences
