from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

from marketmenow.core.feedback.models import VideoMetrics


@runtime_checkable
class VideoAnalyticsFetcher(Protocol):
    """Platform-agnostic protocol for fetching video analytics."""

    async def fetch_channel_videos(
        self,
        *,
        max_results: int = 50,
        published_after: datetime | None = None,
    ) -> list[dict[str, str]]:
        """Return list of dicts with at minimum 'video_id', 'title', 'description', 'published_at'."""
        ...

    async def fetch_video_stats(self, video_ids: list[str]) -> list[VideoMetrics]:
        """Fetch statistics for a batch of video IDs."""
        ...

    async def fetch_comments(
        self,
        video_id: str,
        *,
        max_results: int = 100,
    ) -> list[dict[str, str]]:
        """Return list of dicts with 'comment_id', 'author', 'text', 'like_count', 'published_at'."""
        ...
