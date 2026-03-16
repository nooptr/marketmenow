from __future__ import annotations

from marketmenow.core.orchestrator import CampaignResult, Orchestrator
from marketmenow.core.pipeline import ContentPipeline
from marketmenow.core.scheduler import Scheduler
from marketmenow.models.campaign import (
    Audience,
    Campaign,
    CampaignTarget,
    ScheduleRule,
)
from marketmenow.models.content import (
    BaseContent,
    Carousel,
    CarouselSlide,
    ContentModality,
    DirectMessage,
    MediaAsset,
    Recipient,
    Reel,
    Thread,
    ThreadEntry,
)
from marketmenow.models.result import (
    AnalyticsSnapshot,
    MediaRef,
    PublishResult,
    SendResult,
)
from marketmenow.normaliser import ContentNormaliser, NormalisedContent
from marketmenow.registry import AdapterRegistry, PlatformBundle

__all__ = [
    "AdapterRegistry",
    "AnalyticsSnapshot",
    "Audience",
    "BaseContent",
    "Campaign",
    "CampaignResult",
    "CampaignTarget",
    "Carousel",
    "CarouselSlide",
    "ContentModality",
    "ContentNormaliser",
    "ContentPipeline",
    "DirectMessage",
    "MediaAsset",
    "MediaRef",
    "NormalisedContent",
    "Orchestrator",
    "PlatformBundle",
    "PublishResult",
    "Recipient",
    "Reel",
    "ScheduleRule",
    "Scheduler",
    "SendResult",
    "Thread",
    "ThreadEntry",
]
