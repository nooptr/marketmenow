# Core Framework (src/marketmenow/)

This package is **platform-agnostic**. It must never import from `src/adapters/` or any platform SDK. The only exception is `core/registry_builder.py` which uses lazy imports inside try/except.

## Module Map

| Module                    | Purpose                                                      |
|---------------------------|--------------------------------------------------------------|
| `models/content.py`       | `ContentModality` enum, `BaseContent` and all content variants |
| `models/campaign.py`      | `Audience`, `ScheduleRule`, `CampaignTarget`, `Campaign`     |
| `models/result.py`        | `PublishResult`, `SendResult`, `MediaRef`, `AnalyticsSnapshot` |
| `models/distribution.py`  | `DistributionRoute`, `DistributionMap` (modality → platforms) |
| `ports/platform_adapter.py` | `PlatformAdapter` protocol                                 |
| `ports/content_renderer.py` | `ContentRenderer` protocol                                 |
| `ports/uploader.py`       | `Uploader` protocol                                         |
| `ports/analytics.py`      | `AnalyticsCollector` protocol                                |
| `normaliser.py`           | `NormalisedContent` model + `ContentNormaliser` (match/case dispatch) |
| `registry.py`             | `PlatformBundle` dataclass + `AdapterRegistry`               |
| `exceptions.py`           | `MarketMeNowError` hierarchy (`AdapterNotFoundError`, `UnsupportedModalityError`, `AuthenticationError`, `PublishError`, `RenderError`, `UploadError`) |
| `cli.py`                  | Top-level Typer app (`mmn`) — `distribute`, `platforms`, `version`, platform subcommands |
| `core/pipeline.py`        | `ContentPipeline` — normalise → render → upload → publish    |
| `core/orchestrator.py`    | `Orchestrator` + `CampaignResult` — runs campaigns across targets in parallel |
| `core/distributor.py`     | `ContentDistributor` — resolves platforms from `DistributionMap`, delegates to `Orchestrator` |
| `core/registry_builder.py`| `build_registry()` — auto-registers adapters (lazy imports, graceful skip on missing config) |
| `core/scheduler.py`       | `Scheduler` — in-process scheduled campaign execution        |
| `core/distribute_cli.py`  | Shared async helper for CLI `distribute` command             |
| `integrations/langchain.py`| LangChain tool/chain integration                            |

## Pipeline Flow

```
BaseContent
  → ContentNormaliser.normalise()  →  NormalisedContent
  → bundle.renderer.render()      →  NormalisedContent (platform-adapted)
  → bundle.uploader.upload_batch() →  list[MediaRef] (stored in extra._media_refs)
  → bundle.adapter.publish()       →  PublishResult
```

For `DIRECT_MESSAGE` modality, the last step calls `send_dm()` instead of `publish()`.

## Content Model Hierarchy

All models are `BaseModel` with `frozen=True`. `BaseContent` provides `id` (UUID), `modality`, `created_at`, `metadata`.

Variants: `VideoPost`, `ImagePost`, `Thread` (with `ThreadEntry`), `DirectMessage` (with `Recipient`), `Reply`, `TextPost`, `Document`, `Article`, `Poll`.

## Protocol Signatures

```python
class PlatformAdapter(Protocol):
    platform_name: str                                          # property
    def supported_modalities(self) -> frozenset[ContentModality]: ...
    async def authenticate(self, credentials: dict[str, str]) -> None: ...
    async def publish(self, content: NormalisedContent) -> PublishResult: ...
    async def send_dm(self, content: NormalisedContent) -> SendResult: ...

class ContentRenderer(Protocol):
    platform_name: str                                          # property
    async def render(self, content: NormalisedContent) -> NormalisedContent: ...

class Uploader(Protocol):
    platform_name: str                                          # property
    async def upload(self, asset: MediaAsset) -> MediaRef: ...
    async def upload_batch(self, assets: list[MediaAsset]) -> list[MediaRef]: ...

class AnalyticsCollector(Protocol):
    platform_name: str                                          # property
    async def collect(self, result: PublishResult) -> AnalyticsSnapshot: ...
```

## Registry

`PlatformBundle` groups `adapter`, `renderer`, `uploader`, and optional `analytics`. `AdapterRegistry` stores bundles by platform name and provides `register()`, `get()`, `list_platforms()`, `supports(platform, modality)`.

`build_registry()` in `core/registry_builder.py` calls `_try_<platform>()` for each adapter. Each function does a lazy import, constructs settings from env vars, builds the bundle, and registers it. Exceptions (missing config, validation errors) cause that platform to be silently skipped.

## Key Rules

- Never import platform SDKs or adapter code in this package.
- All data models must be `frozen=True`.
- All protocols use `@runtime_checkable` and structural subtyping (no ABC inheritance).
- Use `model_copy(update={...})` to "mutate" frozen models.
- Normaliser uses `match`/`case` on content type — add a new arm when adding a modality.
