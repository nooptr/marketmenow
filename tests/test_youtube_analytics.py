from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from adapters.youtube.analytics import YouTubeAnalyticsFetcher


@pytest.fixture
def fetcher() -> YouTubeAnalyticsFetcher:
    return YouTubeAnalyticsFetcher(
        client_id="test-client-id",
        client_secret="test-client-secret",
        refresh_token="test-refresh-token",
    )


def _mock_service(
    *,
    channel_items: list[dict[str, object]] | None = None,
    playlist_items: list[dict[str, object]] | None = None,
    video_items: list[dict[str, object]] | None = None,
    comment_items: list[dict[str, object]] | None = None,
) -> MagicMock:
    service = MagicMock()

    # channels().list().execute()
    service.channels.return_value.list.return_value.execute.return_value = {
        "items": channel_items or []
    }

    # playlistItems().list().execute()
    service.playlistItems.return_value.list.return_value.execute.return_value = {
        "items": playlist_items or []
    }

    # videos().list().execute()
    service.videos.return_value.list.return_value.execute.return_value = {
        "items": video_items or []
    }

    # commentThreads().list().execute()
    service.commentThreads.return_value.list.return_value.execute.return_value = {
        "items": comment_items or []
    }

    return service


@patch("adapters.youtube.analytics.build")
async def test_fetch_channel_videos(
    mock_build: MagicMock, fetcher: YouTubeAnalyticsFetcher
) -> None:
    service = _mock_service(
        channel_items=[{"contentDetails": {"relatedPlaylists": {"uploads": "UU_test"}}}],
        playlist_items=[
            {
                "snippet": {
                    "resourceId": {"videoId": "vid1"},
                    "title": "Test Video",
                    "description": "A test",
                    "publishedAt": "2026-03-01T00:00:00Z",
                }
            }
        ],
    )
    mock_build.return_value = service

    videos = await fetcher.fetch_channel_videos(max_results=10)
    assert len(videos) == 1
    assert videos[0]["video_id"] == "vid1"
    assert videos[0]["title"] == "Test Video"


@patch("adapters.youtube.analytics.build")
async def test_fetch_channel_videos_empty_channel(
    mock_build: MagicMock, fetcher: YouTubeAnalyticsFetcher
) -> None:
    service = _mock_service(channel_items=[])
    mock_build.return_value = service
    videos = await fetcher.fetch_channel_videos()
    assert videos == []


@patch("adapters.youtube.analytics.build")
async def test_fetch_channel_videos_filters_by_date(
    mock_build: MagicMock, fetcher: YouTubeAnalyticsFetcher
) -> None:
    service = _mock_service(
        channel_items=[{"contentDetails": {"relatedPlaylists": {"uploads": "UU_test"}}}],
        playlist_items=[
            {
                "snippet": {
                    "resourceId": {"videoId": "old"},
                    "title": "Old",
                    "description": "",
                    "publishedAt": "2024-01-01T00:00:00Z",
                }
            },
            {
                "snippet": {
                    "resourceId": {"videoId": "new"},
                    "title": "New",
                    "description": "",
                    "publishedAt": "2026-03-20T00:00:00Z",
                }
            },
        ],
    )
    mock_build.return_value = service

    videos = await fetcher.fetch_channel_videos(published_after=datetime(2026, 3, 1, tzinfo=UTC))
    assert len(videos) == 1
    assert videos[0]["video_id"] == "new"


@patch("adapters.youtube.analytics.build")
async def test_fetch_video_stats(mock_build: MagicMock, fetcher: YouTubeAnalyticsFetcher) -> None:
    service = _mock_service(
        video_items=[
            {
                "id": "vid1",
                "statistics": {
                    "viewCount": "1500",
                    "likeCount": "120",
                    "commentCount": "8",
                },
            }
        ]
    )
    mock_build.return_value = service

    stats = await fetcher.fetch_video_stats(["vid1"])
    assert len(stats) == 1
    assert stats[0].video_id == "vid1"
    assert stats[0].view_count == 1500
    assert stats[0].like_count == 120
    assert stats[0].comment_count == 8


@patch("adapters.youtube.analytics.build")
async def test_fetch_video_stats_empty(
    mock_build: MagicMock, fetcher: YouTubeAnalyticsFetcher
) -> None:
    stats = await fetcher.fetch_video_stats([])
    assert stats == []


@patch("adapters.youtube.analytics.build")
async def test_fetch_comments(mock_build: MagicMock, fetcher: YouTubeAnalyticsFetcher) -> None:
    service = _mock_service(
        comment_items=[
            {
                "snippet": {
                    "topLevelComment": {
                        "id": "c1",
                        "snippet": {
                            "authorDisplayName": "User1",
                            "textDisplay": "Great video!",
                            "likeCount": 5,
                            "publishedAt": "2026-03-15T12:00:00Z",
                        },
                    }
                }
            }
        ]
    )
    mock_build.return_value = service

    comments = await fetcher.fetch_comments("vid1", max_results=10)
    assert len(comments) == 1
    assert comments[0]["author"] == "User1"
    assert comments[0]["text"] == "Great video!"


@patch("adapters.youtube.analytics.build")
async def test_fetch_comments_handles_disabled(
    mock_build: MagicMock, fetcher: YouTubeAnalyticsFetcher
) -> None:
    service = MagicMock()
    service.commentThreads.return_value.list.return_value.execute.side_effect = Exception(
        "Comments disabled"
    )
    service.close = MagicMock()
    mock_build.return_value = service

    comments = await fetcher.fetch_comments("vid1")
    assert comments == []
