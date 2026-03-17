from __future__ import annotations

from pydantic import BaseModel, Field

from marketmenow.exceptions import UnsupportedModalityError
from marketmenow.models.content import (
    BaseContent,
    Carousel,
    ContentModality,
    DirectMessage,
    MediaAsset,
    Reel,
    Reply,
    Thread,
)


class NormalisedContent(BaseModel, frozen=True):
    """Platform-agnostic envelope that every adapter receives."""

    source: BaseContent
    modality: ContentModality
    text_segments: list[str]
    media_assets: list[MediaAsset]
    hashtags: list[str] = Field(default_factory=list)
    subject: str | None = None
    recipient_handles: list[str] = Field(default_factory=list)
    extra: dict[str, object] = Field(default_factory=dict)


class ContentNormaliser:
    """Converts any BaseContent subclass into a NormalisedContent envelope."""

    def normalise(self, content: BaseContent) -> NormalisedContent:
        match content:
            case Reel():
                return self._normalise_reel(content)
            case Carousel():
                return self._normalise_carousel(content)
            case Thread():
                return self._normalise_thread(content)
            case DirectMessage():
                return self._normalise_dm(content)
            case Reply():
                return self._normalise_reply(content)
            case _:
                raise UnsupportedModalityError(
                    platform="<core>",
                    modality=str(content.modality),
                )

    def _normalise_reel(self, reel: Reel) -> NormalisedContent:
        media: list[MediaAsset] = [reel.video]
        if reel.thumbnail is not None:
            media.append(reel.thumbnail)

        return NormalisedContent(
            source=reel,
            modality=ContentModality.REEL,
            text_segments=[reel.caption] if reel.caption else [],
            media_assets=media,
            hashtags=reel.hashtags,
        )

    def _normalise_carousel(self, carousel: Carousel) -> NormalisedContent:
        text_segments: list[str] = []
        if carousel.caption:
            text_segments.append(carousel.caption)
        for slide in carousel.slides:
            if slide.caption:
                text_segments.append(slide.caption)

        return NormalisedContent(
            source=carousel,
            modality=ContentModality.CAROUSEL,
            text_segments=text_segments,
            media_assets=[slide.media for slide in carousel.slides],
            hashtags=carousel.hashtags,
        )

    def _normalise_thread(self, thread: Thread) -> NormalisedContent:
        text_segments = [entry.text for entry in thread.entries]
        media_assets: list[MediaAsset] = []
        for entry in thread.entries:
            media_assets.extend(entry.media)

        return NormalisedContent(
            source=thread,
            modality=ContentModality.THREAD,
            text_segments=text_segments,
            media_assets=media_assets,
        )

    def _normalise_dm(self, dm: DirectMessage) -> NormalisedContent:
        return NormalisedContent(
            source=dm,
            modality=ContentModality.DIRECT_MESSAGE,
            text_segments=[dm.body],
            media_assets=dm.attachments,
            subject=dm.subject,
            recipient_handles=[r.handle for r in dm.recipients],
        )

    def _normalise_reply(self, reply: Reply) -> NormalisedContent:
        return NormalisedContent(
            source=reply,
            modality=ContentModality.REPLY,
            text_segments=[reply.body],
            media_assets=list(reply.media),
            extra={
                "in_reply_to_url": reply.in_reply_to_url,
                "in_reply_to_platform_id": reply.in_reply_to_platform_id or "",
            },
        )
