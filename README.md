# MarketMeNow

Modular marketing automation framework with a ports-and-adapters architecture.

## Quick Start

```bash
uv sync
```

## Architecture

MarketMeNow uses a **hexagonal / ports-and-adapters** design. The core engine
(orchestrator, pipeline, scheduler) is completely platform-agnostic. Platform
support is added by implementing a set of `typing.Protocol` interfaces and
registering them with the `AdapterRegistry`.

### Content Modalities

| Modality | Class | Description |
|----------|-------|-------------|
| Reel | `Reel` | Short-form video with caption, hashtags, optional thumbnail |
| Carousel | `Carousel` | Multi-slide media post with per-slide captions |
| Thread | `Thread` | Ordered list of text+media entries |
| Direct Message | `DirectMessage` | Private message / cold email with recipients |

### Adding a Platform

1. Implement `PlatformAdapter`, `ContentRenderer`, and `Uploader` protocols.
2. Optionally implement `AnalyticsCollector`.
3. Bundle them into a `PlatformBundle` and register:

```python
from marketmenow import AdapterRegistry, PlatformBundle

registry = AdapterRegistry()
registry.register(PlatformBundle(
    adapter=MyPlatformAdapter(),
    renderer=MyPlatformRenderer(),
    uploader=MyPlatformUploader(),
))
```

### Adding a Content Modality

1. Add a variant to `ContentModality` in `models/content.py`.
2. Create a frozen Pydantic model inheriting `BaseContent`.
3. Add a `case` arm in `ContentNormaliser.normalise()`.

### Running a Campaign

```python
import asyncio
from marketmenow import (
    Campaign, CampaignTarget, ContentModality,
    Orchestrator, AdapterRegistry, Reel, MediaAsset,
)

registry = AdapterRegistry()
# ... register platform bundles ...

orchestrator = Orchestrator(registry)

campaign = Campaign(
    name="Launch Video",
    content=Reel(
        video=MediaAsset(uri="https://cdn.example.com/video.mp4", mime_type="video/mp4"),
        caption="Check this out!",
        hashtags=["#launch", "#new"],
    ),
    targets=[
        CampaignTarget(platform="instagram", modality=ContentModality.REEL),
        CampaignTarget(platform="linkedin", modality=ContentModality.REEL),
    ],
)

result = asyncio.run(orchestrator.run_campaign(campaign))
```
