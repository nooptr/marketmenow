from __future__ import annotations

import enum
from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ContentModality(str, enum.Enum):
    REEL = "reel"
    CAROUSEL = "carousel"
    THREAD = "thread"
    DIRECT_MESSAGE = "direct_message"


class MediaAsset(BaseModel, frozen=True):
    """A single media file reference -- local path or remote URL."""

    uri: str
    mime_type: str
    alt_text: str = ""
    duration_seconds: float | None = None
    width: int | None = None
    height: int | None = None


class BaseContent(BaseModel, frozen=True):
    """Abstract base for all content modalities."""

    id: UUID = Field(default_factory=uuid4)
    modality: ContentModality
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, str] = Field(default_factory=dict)


class Reel(BaseContent):
    modality: ContentModality = ContentModality.REEL
    video: MediaAsset
    caption: str = ""
    hashtags: list[str] = Field(default_factory=list)
    thumbnail: MediaAsset | None = None


class CarouselSlide(BaseModel, frozen=True):
    media: MediaAsset
    caption: str = ""


class Carousel(BaseContent):
    modality: ContentModality = ContentModality.CAROUSEL
    slides: list[CarouselSlide] = Field(..., min_length=2)
    caption: str = ""
    hashtags: list[str] = Field(default_factory=list)


class ThreadEntry(BaseModel, frozen=True):
    text: str
    media: list[MediaAsset] = Field(default_factory=list)


class Thread(BaseContent):
    modality: ContentModality = ContentModality.THREAD
    entries: list[ThreadEntry] = Field(..., min_length=1)


class Recipient(BaseModel, frozen=True):
    handle: str
    platform_id: str | None = None


class DirectMessage(BaseContent):
    modality: ContentModality = ContentModality.DIRECT_MESSAGE
    recipients: list[Recipient] = Field(..., min_length=1)
    subject: str | None = None
    body: str
    attachments: list[MediaAsset] = Field(default_factory=list)
