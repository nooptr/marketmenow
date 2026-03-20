# MarketMeNow

Cross-platform marketing automation framework. Generates and publishes content across Instagram, Twitter/X, Reddit, LinkedIn, YouTube, and Email from a single CLI or web dashboard.

## Project Layout

```
src/marketmenow/          # Platform-agnostic core (models, ports, pipeline, registry)
src/adapters/             # Platform-specific adapters (instagram, twitter, linkedin, reddit, email, facebook, youtube)
src/web/                  # FastAPI web dashboard
tests/                    # pytest + pytest-asyncio test suite
prompts/                  # YAML prompt templates per platform
pyproject.toml            # Single source of truth for deps, scripts, ruff, pytest config
```

## Commands

```bash
uv sync                              # Install dependencies
uv sync --all-extras                  # Install with optional deps (langchain, dev tools)
uv run --extra dev pytest             # Run tests
uv run ruff check src/ tests/        # Lint
uv run ruff format src/ tests/       # Format
uv run ruff check --fix src/ tests/  # Auto-fix safe lint issues
uv run mmn --help                    # CLI help
uv run mmn-web                       # Start web dashboard (http://localhost:8000)
docker compose up -d                 # Start PostgreSQL (required for web dashboard)
```

## Architecture

Ports-and-adapters (hexagonal). The core engine is completely platform-agnostic.

**Pipeline flow:** Content → Normalise → Render → Upload → Publish

Key components:
- `ContentPipeline` (`core/pipeline.py`) — executes the four-stage pipeline for one platform
- `Orchestrator` (`core/orchestrator.py`) — runs a Campaign across multiple targets via `asyncio.gather`
- `ContentDistributor` (`core/distributor.py`) — resolves target platforms from a `DistributionMap` then delegates to `Orchestrator`
- `AdapterRegistry` (`registry.py`) — holds `PlatformBundle` instances keyed by platform name
- `ContentNormaliser` (`normaliser.py`) — converts any `BaseContent` variant into `NormalisedContent`
- `build_registry()` (`core/registry_builder.py`) — auto-registers all adapters whose env vars are present

### Protocols (ports/)

All defined as `typing.Protocol` with `@runtime_checkable`:

- **`PlatformAdapter`** — `platform_name`, `supported_modalities()`, `authenticate()`, `publish()`, `send_dm()`
- **`ContentRenderer`** — `platform_name`, `render(NormalisedContent) -> NormalisedContent`
- **`Uploader`** — `platform_name`, `upload(MediaAsset) -> MediaRef`, `upload_batch()`
- **`AnalyticsCollector`** — `platform_name`, `collect(PublishResult) -> AnalyticsSnapshot`

### Content Models (models/content.py)

`ContentModality` enum: VIDEO, IMAGE, THREAD, DIRECT_MESSAGE, REPLY, TEXT_POST, DOCUMENT, ARTICLE, POLL

`BaseContent` → `VideoPost`, `ImagePost`, `Thread`, `DirectMessage`, `Reply`, `TextPost`, `Document`, `Article`, `Poll`

### Adapters (src/adapters/)

| Adapter    | Modalities                                    | Key subsystems                                    |
|------------|-----------------------------------------------|---------------------------------------------------|
| instagram  | VIDEO, IMAGE                                  | Reels (TTS + Remotion), Carousels, Figma export   |
| twitter    | THREAD, REPLY                                 | Discovery, reply generation, engagement orchestrator |
| linkedin   | TEXT_POST, IMAGE, VIDEO, DOCUMENT, ARTICLE, POLL | API + browser posting                            |
| reddit     | REPLY                                         | Two-phase: discover → generate comments           |
| youtube    | VIDEO                                         | Shorts upload via Data API v3                     |
| email      | DIRECT_MESSAGE                                | CSV + Jinja2 templates, Gemini paraphrasing       |
| facebook   | (planned)                                     | Browser-based posting                             |

## Architecture Rules

1. **Core is platform-agnostic.** `src/marketmenow/` must never import from `src/adapters/` or any platform SDK. The only exception is `core/registry_builder.py` which does lazy imports inside try/except blocks.
2. **Structural subtyping only.** Adapters implement `typing.Protocol` interfaces — never subclass an ABC.
3. **Immutable data.** All Pydantic models use `frozen=True`. Mutate via `model_copy(update={...})`.
4. **Adapters are independent.** Adapter packages must not import from each other.
5. **`PlatformBundle` registration.** Each adapter exposes a `create_*_bundle(settings)` factory. Registration happens in `core/registry_builder.py` — missing env vars cause graceful skip.

## Python Style

- Python >= 3.12. `from __future__ import annotations` in every file.
- Full type annotations everywhere. Never use `Any`.
- Async-first: adapter methods are `async def`.
- Pydantic `BaseModel` with `frozen=True` for all data models.
- `typing.Protocol` with `@runtime_checkable` for all adapter interfaces.
- Absolute imports, no circular dependencies.

## Testing

- Tests in `tests/`, one `test_*.py` per module.
- Naming: `test_{module}_{behavior}`.
- `conftest.py` provides `MockAdapter`, `MockRenderer`, `MockUploader`, `MockAnalytics`, content factories (`make_video`, `make_image`, `make_thread`, etc.), and a pre-built `AdapterRegistry`.
- pytest-asyncio with `asyncio_mode = "auto"` — async tests are plain `async def`, no decorator.
- **Never call external APIs in tests.** Mock all I/O.
- Use `pytest.raises()` for expected exceptions, `tmp_path` for file-system tests.

## Adding a New Platform

1. Create `src/adapters/yourplatform/` with `adapter.py`, `renderer.py`, `uploader.py`, `settings.py`.
2. Implement `PlatformAdapter`, `ContentRenderer`, `Uploader` protocols.
3. Optionally implement `AnalyticsCollector`.
4. Expose `create_yourplatform_bundle(settings) -> PlatformBundle` in `__init__.py`.
5. Add a `_try_yourplatform()` function in `core/registry_builder.py`.
6. No changes to `core/`, `models/`, or `ports/`.

## Adding a New Content Modality

1. Add variant to `ContentModality` enum in `models/content.py`.
2. Create frozen Pydantic model inheriting `BaseContent`.
3. Add `case` arm in `ContentNormaliser.normalise()`.
4. Existing adapters update their `supported_modalities()`.

## Web Dashboard (src/web/)

FastAPI app with Jinja2 templates. Runs `mmn` CLI commands as subprocesses via `cli_runner.py`. The queue worker (`queue_worker.py`) drains a per-platform posting queue with rate limiting. Real-time progress via WebSocket (`/ws/content/{item_id}`) and `EventHub`.

## Environment

- Copy `.env.example` to `.env` and fill in API keys for platforms you use.
- `uv` is the package manager. All deps in `pyproject.toml`.
- Docker Compose provides PostgreSQL for the web dashboard.

## Commit Messages

Use conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`.
