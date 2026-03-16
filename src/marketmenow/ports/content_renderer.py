from __future__ import annotations

from typing import Protocol, runtime_checkable

from marketmenow.normaliser import NormalisedContent


@runtime_checkable
class ContentRenderer(Protocol):
    @property
    def platform_name(self) -> str: ...

    async def render(self, content: NormalisedContent) -> NormalisedContent:
        """Transform normalised content into platform-specific form.

        May adjust text_segments (add platform hashtag syntax), resize media
        references, inject platform-required metadata into ``extra``, etc.
        Returns a **new** NormalisedContent instance.
        """
        ...
