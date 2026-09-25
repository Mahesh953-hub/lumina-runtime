# Lumina implementation plan

## Product boundary

Lumina is a multimodal execution runtime for agents that do not natively process pixels. It exposes a narrow, declarative tool boundary and a provider boundary for neural image engines.

## Delivered

- [x] Deterministic Pillow/NumPy canvas
- [x] Image decoding and bounded resource checks
- [x] Color, geometry, brightness, contrast, entropy, and dynamic-range observations
- [x] Allow-listed edit operations
- [x] Bounded image revision loop
- [x] OpenAI-compatible external generation provider
- [x] FastAPI JSON API and OpenAPI documentation
- [x] Python package and CLI
- [x] Tests, linting, Docker packaging, and CI

## Extension architecture

- Add neural vision providers by implementing a provider with `generate` or `analyze` and returning observations in the same contract.
- Add SVG/HTML rendering as a deterministic creation backend.
- Add OpenCV-specific operations such as contour extraction and segmentation without exposing shell execution.
- Add MCP as an adapter over the HTTP API; keep the API as the canonical contract.

## Security invariants

- No agent-supplied Python, shell commands, URLs, or filesystem paths.
- Allow-listed edits only.
- Bounded dimensions, decoded pixels, and input bytes.
- Opaque generated artifact IDs.
- Provider keys read only from environment variables.
