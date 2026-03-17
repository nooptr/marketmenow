from __future__ import annotations

from marketmenow.normaliser import NormalisedContent

_LI_MAX_POST_LENGTH = 3000
_LI_MAX_IMAGES = 20
_LI_MAX_DOC_PAGES = 300


class LinkedInRenderer:
    """Enforces LinkedIn constraints on normalised content."""

    @property
    def platform_name(self) -> str:
        return "linkedin"

    async def render(self, content: NormalisedContent) -> NormalisedContent:
        hashtags = [tag.lstrip("#") for tag in content.hashtags]
        text_segments = list(content.text_segments)

        hashtag_str = " ".join(f"#{t}" for t in hashtags) if hashtags else ""
        total_text_len = sum(len(s) for s in text_segments)
        separator_len = 2 if hashtag_str else 0

        if total_text_len + separator_len + len(hashtag_str) > _LI_MAX_POST_LENGTH:
            budget = _LI_MAX_POST_LENGTH - separator_len - len(hashtag_str)
            if budget < 0:
                hashtags = hashtags[:5]
                hashtag_str = " ".join(f"#{t}" for t in hashtags)
                budget = _LI_MAX_POST_LENGTH - 2 - len(hashtag_str)
            truncated: list[str] = []
            remaining = budget
            for seg in text_segments:
                if remaining <= 0:
                    break
                if len(seg) <= remaining:
                    truncated.append(seg)
                    remaining -= len(seg)
                else:
                    truncated.append(seg[: remaining - 3] + "...")
                    remaining = 0
            text_segments = truncated

        media_assets = content.media_assets
        from marketmenow.models.content import ContentModality

        if content.modality == ContentModality.IMAGE:
            media_assets = media_assets[:_LI_MAX_IMAGES]

        return content.model_copy(
            update={
                "text_segments": text_segments,
                "hashtags": hashtags,
                "media_assets": media_assets,
            }
        )
