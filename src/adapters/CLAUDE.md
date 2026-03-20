# Adapters (src/adapters/)

Platform-specific implementations. Each adapter package is independent and must not import from other adapter packages.

## Implemented Adapters

| Package      | Modalities                                     | Bundle factory                   |
|--------------|------------------------------------------------|----------------------------------|
| `instagram/` | VIDEO, IMAGE                                   | `create_instagram_bundle()`      |
| `twitter/`   | THREAD, REPLY                                  | `create_twitter_bundle()`        |
| `linkedin/`  | TEXT_POST, IMAGE, VIDEO, DOCUMENT, ARTICLE, POLL | `create_linkedin_bundle()`     |
| `reddit/`    | REPLY                                          | `create_reddit_bundle()`         |
| `youtube/`   | VIDEO                                          | `create_youtube_bundle()`        |
| `email/`     | DIRECT_MESSAGE                                 | `create_email_bundle()`          |
| `facebook/`  | (planned)                                      | `create_facebook_bundle()`       |

## Standard Adapter Structure

```
adapters/yourplatform/
├── __init__.py      # create_yourplatform_bundle(settings) -> PlatformBundle
├── adapter.py       # PlatformAdapter protocol implementation
├── renderer.py      # ContentRenderer protocol implementation
├── uploader.py      # Uploader protocol implementation
├── settings.py      # pydantic-settings for env vars (BaseSettings)
└── cli.py           # Typer sub-commands (optional)
```

## Protocols to Implement

From `marketmenow.ports`:
- `PlatformAdapter` — `platform_name`, `supported_modalities()`, `authenticate()`, `publish()`, `send_dm()`
- `ContentRenderer` — `platform_name`, `render(NormalisedContent) -> NormalisedContent`
- `Uploader` — `platform_name`, `upload(MediaAsset) -> MediaRef`, `upload_batch()`
- `AnalyticsCollector` (optional) — `platform_name`, `collect(PublishResult) -> AnalyticsSnapshot`

Use structural subtyping — just implement the methods, never subclass the Protocol.

## Bundle Registration

Each adapter exposes a factory in `__init__.py`:

```python
def create_yourplatform_bundle(settings: YourSettings | None = None) -> PlatformBundle:
    if settings is None:
        settings = YourSettings()
    return PlatformBundle(
        adapter=YourAdapter(settings),
        renderer=YourRenderer(),
        uploader=YourUploader(settings),
    )
```

Registration happens in `marketmenow/core/registry_builder.py` via a `_try_yourplatform()` function that does a lazy import, constructs settings, builds the bundle, and calls `registry.register()`. Missing env vars cause graceful skip.

## Complex Subsystems

### Instagram Reels (`instagram/reels/`)

Full video generation pipeline: template loading → AI script generation → TTS (ElevenLabs/OpenAI/Kokoro) → Remotion render → `.mp4`. Orchestrated by `ReelOrchestrator`. Templates are YAML-driven with pluggable pipeline steps (`StepRegistry`).

### Instagram Carousels (`instagram/carousel/`)

Multi-image generation via Imagen + Pillow compositing.

### Twitter Engagement (`twitter/orchestrator.py`)

Discovery (handles + hashtags → posts) → LLM reply generation → human approval callback → Playwright posting. Includes `PerformanceTracker` and caching.

### Reddit Two-Phase (`reddit/orchestrator.py`)

Phase 1: `mmn reddit engage` — discover subreddits, generate comments to CSV.
Phase 2: `mmn reddit reply -f comments.csv` — post from the CSV.

### LinkedIn (`linkedin/`)

Dual mode: API adapter (`api_adapter.py` + `api_client.py`) or browser-based (`browser.py`). Content generation via `content_generator.py`.

## Environment Variables

Each adapter reads credentials from env vars via pydantic-settings. See `.env.example` for the full list. Adapters whose env vars are missing are silently skipped by `build_registry()`.

## Key Rules

- Never import between adapter packages.
- All adapter methods are `async def`.
- Settings use pydantic `BaseSettings` reading from environment.
- Browser automation uses Playwright (chromium).
- CLI subcommands use Typer, registered in `marketmenow/cli.py`.
