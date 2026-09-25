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

- [x] Compare two images and return pixel mismatch, RMS, mean absolute error, and a bounded difference artifact
- [x] Retrieve artifacts by opaque ID and return metadata without exposing arbitrary filesystem paths
- [x] Publish a Python client SDK for create, analyze, compare, edit, revise, and artifact download
- [x] Add tests for malformed Base64, mismatched dimensions, missing artifacts, and traversal-safe artifact lookup
- [x] Verify the complete repository, commit, and push this phase without the CI workflow

Acceptance:

1. Compare responses distinguish identical images from changed images.
2. Different-sized inputs are handled by an explicit documented policy rather than an accidental crash.
3. Artifact IDs can retrieve only generated files and metadata.
4. The SDK talks to the HTTP contract rather than bypassing it with server internals.
5. Ruff, Bandit, and all tests pass locally.

Phase 2 acceptance:

1. Job records survive process restarts in SQLite and interrupted running jobs are requeued.
2. A separate worker can create, analyze, compare, edit, and revise artifacts.
3. Cancellation is terminal and progress events remain replayable.
4. Semantic feedback has a typed provider contract and a quality gate.
5. MCP tool names are translated through the canonical HTTP boundary.

## Phase 2 — long-running and semantic execution

Goal: let agents run expensive work asynchronously and improve outputs using semantic feedback.

- [x] Add durable job records with `queued`, `running`, `completed`, `failed`, and `canceled` states
- [x] Add worker execution, progress events, cancellation, and restart recovery
- [x] Add a semantic vision-provider contract for captions, objects, OCR, relationships, and required-element coverage
- [x] Add quality gates and bounded automatic revision until requirements pass
- [x] Add MCP as an adapter over the canonical HTTP API

Design constraints:

- A worker must not be implemented as an unbounded thread inside the web process.
- Provider calls must remain behind the HTTPS-only, resource-bounded provider boundary.
- Job payloads must not contain unvalidated executable code or provider secrets.
- Progress events must be replayable after reconnecting.

## Phase 3 — compositional visual work

Goal: represent visual work as editable, layered scenes rather than only flattened PNG artifacts.

- [x] Define a bounded scene document with canvas, layers, transforms, masks, and asset references
- [x] Compose deterministic rectangle, ellipse, and text layers
- [x] Replace one scene layer without recreating the entire scene model
- [x] Export scenes to PNG, JPEG, WebP, SVG, and PDF where supported
- [x] Add scene validation and render tests
- [x] Add richer masks and transforms

## Phase 4 — production deployment

Goal: operate Lumina safely for multiple users and long-running workloads.

- [x] Add authentication, tenant isolation, quotas, rate limits, and provider-cost limits
- [x] Add an optional API-key authentication boundary
- [x] Add multi-tenant request identity, rate limits, and policy checks
- [x] Add provider-cost accounting policy primitives
- [x] Add a local storage adapter and production storage contract
- [x] Add metrics and health/readiness-style runtime information
- [x] Add storage adapters for local and S3-compatible object stores
- [x] Add PostgreSQL and in-memory metadata store contracts
- [x] Add traces, structured logs, and audit events
- [x] Add retention policies
- [x] Add provider retry budgets, circuit breakers, and idempotency keys
- [x] Add end-to-end API, security, and concurrent execution tests

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
