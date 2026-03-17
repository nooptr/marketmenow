from __future__ import annotations

from marketmenow.normaliser import NormalisedContent


class TwitterRenderer:
    """Enforces Twitter/X constraints on normalised content."""

    @property
    def platform_name(self) -> str:
        return "twitter"

    async def render(self, content: NormalisedContent) -> NormalisedContent:
        truncated_segments: list[str] = []
        for segment in content.text_segments:
            if len(segment) > 280:
                segment = segment[:277] + "..."
            truncated_segments.append(segment)

        return content.model_copy(update={"text_segments": truncated_segments})
