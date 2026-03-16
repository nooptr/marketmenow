from __future__ import annotations

from marketmenow.models.content import ContentModality
from marketmenow.normaliser import NormalisedContent

_IG_MAX_CAPTION = 2200
_IG_CAROUSEL_MAX_SLIDES = 10

_ASPECT_RATIOS: dict[ContentModality, dict[str, float]] = {
    ContentModality.REEL: {"width": 1080, "height": 1920},
    ContentModality.CAROUSEL: {"width": 1080, "height": 1080},
}


class InstagramRenderer:
    """Satisfies ``ContentRenderer`` protocol -- Instagram-specific transforms."""

    @property
    def platform_name(self) -> str:
        return "instagram"

    async def render(self, content: NormalisedContent) -> NormalisedContent:
        hashtags = [tag.lstrip("#") for tag in content.hashtags]
        text_segments = list(content.text_segments)

        if text_segments:
            total_len = sum(len(s) for s in text_segments)
            hashtag_str = " ".join(f"#{t}" for t in hashtags)
            if total_len + len(hashtag_str) + 2 > _IG_MAX_CAPTION:
                overflow = (total_len + len(hashtag_str) + 2) - _IG_MAX_CAPTION
                last = text_segments[-1]
                text_segments[-1] = last[: max(0, len(last) - overflow)]

        extra = dict(content.extra)
        if content.modality in _ASPECT_RATIOS:
            extra["ig_aspect"] = _ASPECT_RATIOS[content.modality]

        media_assets = content.media_assets
        if content.modality == ContentModality.CAROUSEL:
            media_assets = media_assets[:_IG_CAROUSEL_MAX_SLIDES]

        return content.model_copy(
            update={
                "text_segments": text_segments,
                "hashtags": hashtags,
                "media_assets": media_assets,
                "extra": extra,
            }
        )
