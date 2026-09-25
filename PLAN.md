# Lumina phased roadmap

This roadmap is the implementation backlog for Lumina. A checked item means its behavior is implemented and verified by the repository's test suite. A planned item is not a delivered feature.

## Product definition

Lumina is a multimodal execution runtime for text-only agents. It exposes safe, structured tools for image creation, observation, editing, comparison, retrieval, planning, and long-running execution. Lumina does not claim to make a language model natively multimodal; it provides mediated visual tools and feedback.

## Current baseline

- [x] Deterministic Pillow/NumPy canvas
- [x] Bounded image decoding and artifact storage
- [x] Color, geometry, brightness, contrast, and entropy observations
- [x] Allow-listed drawing and filter operations
- [x] Bounded deterministic revision
- [x] OpenAI-compatible image-generation adapter
- [x] FastAPI JSON/OpenAPI contract, package, CLI, and Docker packaging
- [x] Security controls, tests, linting, and beginner documentation

## Phase 0 — explain and operate the runtime

- [x] Publish `NOOB_GUIDE.md` with installation, concepts, API examples, and troubleshooting
- [x] Record the product architecture and security invariants
- [x] Define incremental acceptance phases instead of placeholder architecture

## Phase 1 — practical visual utility

Goal: make Lumina useful for building, evaluating, and retrieving ordinary images without a diffusion model.

- [ ] Compare two images and return pixel mismatch, RMS, mean absolute error, and a bounded difference artifact
- [ ] Retrieve artifacts by opaque ID and return metadata without exposing arbitrary filesystem paths
- [ ] Publish a Python client SDK for create, analyze, compare, edit, revise, and artifact download
- [ ] Add tests for malformed Base64, mismatched dimensions, missing artifacts, and traversal-safe artifact lookup
- [ ] Verify the complete repository, commit, and push this phase without the CI workflow

Acceptance:

1. Compare responses distinguish identical images from changed images.
2. Different-sized inputs are handled by an explicit documented policy rather than an accidental crash.
3. Artifact IDs can retrieve only generated files and metadata.
4. The SDK talks to the HTTP contract rather than bypassing it with server internals.
5. Ruff, Bandit, and all tests pass locally.

## Phase 2 — long-running and semantic execution

Goal: let agents run expensive work asynchronously and improve outputs using semantic feedback.

- [ ] Add durable job records with `queued`, `running`, `completed`, `failed`, and `canceled` states
- [ ] Add worker execution, progress events, cancellation, and restart recovery
- [ ] Add a semantic vision-provider contract for captions, objects, OCR, relationships, and required-element coverage
- [ ] Add quality gates and bounded automatic revision until requirements pass
- [ ] Add MCP as an adapter over the canonical HTTP API

Design constraints:

- A worker must not be implemented as an unbounded thread inside the web process.
- Provider calls must remain behind the HTTPS-only, resource-bounded provider boundary.
- Job payloads must not contain unvalidated executable code or provider secrets.
- Progress events must be replayable after reconnecting.

## Phase 3 — compositional visual work

Goal: represent visual work as editable, layered scenes rather than only flattened PNG artifacts.

- [ ] Define a bounded scene document with canvas, layers, transforms, masks, and asset references
- [ ] Compose deterministic layers: rectangles, ellipses, text, charts, SVG, and generated assets
- [ ] Regenerate or replace one scene layer without recreating the entire image
- [ ] Export scenes to PNG, JPEG, WebP, SVG, and PDF where supported
- [ ] Add scene validation and render tests

## Phase 4 — production deployment

Goal: operate Lumina safely for multiple users and long-running workloads.

- [ ] Add authentication, tenant isolation, quotas, rate limits, and provider-cost limits
- [ ] Add PostgreSQL metadata and S3-compatible artifact storage adapters
- [ ] Add metrics, traces, structured logs, audit events, and health/readiness probes
- [ ] Add migration and retention policies
- [ ] Add provider failover, retry budgets, circuit breakers, and idempotency keys
- [ ] Add end-to-end security and load tests

## Explicitly out of scope for the next milestone

- Training a foundation image or vision model
- Arbitrary Python or shell execution for agents
- Public multi-tenant hosting before auth, quotas, and storage isolation exist
- A large media suite (video, 3D, audio) before durable jobs and scene composition work

## Security invariants

These are not optional backlog items:

- No agent-supplied Python, shell commands, URLs, or filesystem paths.
- Allow-listed edits only.
- Bounded dimensions, decoded pixels, upload bytes, provider responses, and revision count.
- Opaque generated artifact IDs and traversal-safe lookup.
- Provider keys read only from environment variables.
- External providers require HTTPS.

## Contribution loop

For every vertical slice:

1. Write a failing behavior test.
2. Run it and confirm the expected failure.
3. Implement the smallest complete behavior.
4. Run focused tests, full tests, Ruff, and Bandit.
5. Update this roadmap and relevant documentation.
6. Commit the verified milestone and push it while keeping the CI workflow out of the pushed tree unless GitHub write scope is available.
