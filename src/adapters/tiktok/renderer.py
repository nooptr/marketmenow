from __future__ import annotations

from marketmenow.normaliser import NormalisedContent

_TT_MAX_CAPTION = 2200


class TikTokRenderer:
    """Satisfies ``ContentRenderer`` protocol -- TikTok-specific transforms."""

    @property
    def platform_name(self) -> str:
        return "tiktok"

    async def render(self, content: NormalisedContent) -> NormalisedContent:
        hashtags = [tag.lstrip("#") for tag in content.hashtags]

        text_segments = list(content.text_segments)
        if text_segments:
            hashtag_str = " ".join(f"#{t}" for t in hashtags)
            total_len = sum(len(s) for s in text_segments) + len(hashtag_str) + 2
            if total_len > _TT_MAX_CAPTION:
                overflow = total_len - _TT_MAX_CAPTION
                last = text_segments[-1]
                text_segments[-1] = last[: max(0, len(last) - overflow)]

        return content.model_copy(
            update={
                "text_segments": text_segments,
                "hashtags": hashtags,
            }
        )
