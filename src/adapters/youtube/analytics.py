from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from functools import partial

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from marketmenow.core.feedback.models import VideoMetrics

_YOUTUBE_API_SERVICE = "youtube"
_YOUTUBE_API_VERSION = "v3"
_SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
_TOKEN_URI = "https://oauth2.googleapis.com/token"

_MAX_BATCH = 50  # YouTube API limit for videos().list() id parameter

logger = logging.getLogger(__name__)


class YouTubeAnalyticsFetcher:
    """Fetches video analytics from YouTube Data API v3.

    Satisfies the ``VideoAnalyticsFetcher`` protocol defined in
    ``marketmenow.core.feedback.ports``.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        refresh_token: str,
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._refresh_token = refresh_token

    def _build_credentials(self) -> Credentials:
        return Credentials(
            token=None,
            refresh_token=self._refresh_token,
            token_uri=_TOKEN_URI,
            client_id=self._client_id,
            client_secret=self._client_secret,
            scopes=_SCOPES,
        )

    def _build_service(self) -> object:
        creds = self._build_credentials()
        return build(_YOUTUBE_API_SERVICE, _YOUTUBE_API_VERSION, credentials=creds)

    async def fetch_channel_videos(
        self,
        *,
        max_results: int = 50,
        published_after: datetime | None = None,
    ) -> list[dict[str, str]]:
        """List videos from the authenticated channel's uploads playlist."""
        loop = asyncio.get_running_loop()
        service = self._build_service()

        try:
            # Get the uploads playlist ID
            channels_resp = await loop.run_in_executor(
                None,
                partial(
                    service.channels()  # type: ignore[union-attr]
                    .list(part="contentDetails", mine=True)
                    .execute
                ),
            )
            items = channels_resp.get("items", [])
            if not items:
                return []

            uploads_playlist_id = items[0]["contentDetails"]["relatedPlaylists"]["uploads"]

            # Paginate through the uploads playlist
            videos: list[dict[str, str]] = []
            page_token: str | None = None
            remaining = max_results

            while remaining > 0:
                page_size = min(remaining, 50)
                request_kwargs: dict[str, object] = {
                    "part": "snippet",
                    "playlistId": uploads_playlist_id,
                    "maxResults": page_size,
                }
                if page_token:
                    request_kwargs["pageToken"] = page_token

                resp = await loop.run_in_executor(
                    None,
                    partial(
                        service.playlistItems()  # type: ignore[union-attr]
                        .list(**request_kwargs)
                        .execute
                    ),
                )

                for item in resp.get("items", []):
                    snippet = item.get("snippet", {})
                    published_at_str = snippet.get("publishedAt", "")

                    # Filter by published_after if provided
                    if published_after and published_at_str:
                        try:
                            pub_dt = datetime.fromisoformat(published_at_str.replace("Z", "+00:00"))
                            if pub_dt < published_after:
                                continue
                        except ValueError:
                            pass

                    video_id = snippet.get("resourceId", {}).get("videoId", "")
                    if video_id:
                        videos.append(
                            {
                                "video_id": video_id,
                                "title": snippet.get("title", ""),
                                "description": snippet.get("description", ""),
                                "published_at": published_at_str,
                            }
                        )

                remaining -= page_size
                page_token = resp.get("nextPageToken")
                if not page_token:
                    break

            return videos[:max_results]
        finally:
            service.close()  # type: ignore[union-attr]

    async def fetch_video_stats(self, video_ids: list[str]) -> list[VideoMetrics]:
        """Fetch statistics for a batch of video IDs (batched at 50)."""
        if not video_ids:
            return []

        loop = asyncio.get_running_loop()
        service = self._build_service()
        now = datetime.now(UTC)
        results: list[VideoMetrics] = []

        try:
            for i in range(0, len(video_ids), _MAX_BATCH):
                batch = video_ids[i : i + _MAX_BATCH]
                resp = await loop.run_in_executor(
                    None,
                    partial(
                        service.videos()  # type: ignore[union-attr]
                        .list(part="statistics", id=",".join(batch))
                        .execute
                    ),
                )

                for item in resp.get("items", []):
                    stats = item.get("statistics", {})
                    results.append(
                        VideoMetrics(
                            video_id=item["id"],
                            view_count=int(stats.get("viewCount", 0)),
                            like_count=int(stats.get("likeCount", 0)),
                            comment_count=int(stats.get("commentCount", 0)),
                            collected_at=now,
                        )
                    )

            return results
        finally:
            service.close()  # type: ignore[union-attr]

    async def fetch_comments(
        self,
        video_id: str,
        *,
        max_results: int = 100,
    ) -> list[dict[str, str]]:
        """Fetch top-level comments for a video."""
        loop = asyncio.get_running_loop()
        service = self._build_service()
        comments: list[dict[str, str]] = []

        try:
            page_token: str | None = None
            remaining = max_results

            while remaining > 0:
                page_size = min(remaining, 100)
                request_kwargs: dict[str, object] = {
                    "part": "snippet",
                    "videoId": video_id,
                    "maxResults": page_size,
                    "order": "relevance",
                    "textFormat": "plainText",
                }
                if page_token:
                    request_kwargs["pageToken"] = page_token

                try:
                    resp = await loop.run_in_executor(
                        None,
                        partial(
                            service.commentThreads()  # type: ignore[union-attr]
                            .list(**request_kwargs)
                            .execute
                        ),
                    )
                except Exception:
                    logger.warning(
                        "Failed to fetch comments for video %s (comments may be disabled)",
                        video_id,
                    )
                    break

                for item in resp.get("items", []):
                    top = item.get("snippet", {}).get("topLevelComment", {})
                    snippet = top.get("snippet", {})
                    comments.append(
                        {
                            "comment_id": top.get("id", ""),
                            "author": snippet.get("authorDisplayName", ""),
                            "text": snippet.get("textDisplay", ""),
                            "like_count": str(snippet.get("likeCount", 0)),
                            "published_at": snippet.get("publishedAt", ""),
                        }
                    )

                remaining -= page_size
                page_token = resp.get("nextPageToken")
                if not page_token:
                    break

            return comments[:max_results]
        finally:
            service.close()  # type: ignore[union-attr]
