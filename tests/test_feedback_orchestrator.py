from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from marketmenow.core.feedback.models import CommentData, ContentGuideline, VideoMetrics
from marketmenow.core.feedback.orchestrator import FeedbackOrchestrator


def _make_fetcher(
    *,
    videos: list[dict[str, str]] | None = None,
    stats: list[VideoMetrics] | None = None,
    comments: list[dict[str, str]] | None = None,
) -> MagicMock:
    fetcher = MagicMock()
    fetcher.fetch_channel_videos = AsyncMock(return_value=videos or [])
    fetcher.fetch_video_stats = AsyncMock(return_value=stats or [])
    fetcher.fetch_comments = AsyncMock(return_value=comments or [])
    return fetcher


def _make_scorer(scored: list[CommentData] | None = None) -> MagicMock:
    scorer = MagicMock()
    scorer.score_comments = AsyncMock(return_value=scored or [])
    return scorer


def _make_generator(guidelines: list[ContentGuideline] | None = None) -> MagicMock:
    gen = MagicMock()
    gen.analyze_reel = AsyncMock(return_value=guidelines or [])
    return gen


async def test_empty_channel(tmp_path: Path) -> None:
    orch = FeedbackOrchestrator(
        fetcher=_make_fetcher(),
        sentiment_scorer=_make_scorer(),
        guideline_generator=_make_generator(),
        project_slug="test",
        project_root=tmp_path,
    )
    report = await orch.run_feedback_cycle()
    assert report.reels_analyzed == 0


async def test_full_cycle_creates_files(tmp_path: Path) -> None:
    videos = [
        {
            "video_id": "vid1",
            "title": "Test Video",
            "description": "Description",
            "published_at": "2026-03-01T00:00:00Z",
        }
    ]
    stats = [VideoMetrics(video_id="vid1", view_count=100, like_count=5, comment_count=2)]
    raw_comments = [
        {"comment_id": "c1", "author": "User", "text": "Bad", "like_count": "0", "published_at": ""}
    ]
    scored = [
        CommentData(
            comment_id="c1",
            author="User",
            text="Bad",
            sentiment_score=2.0,
            sentiment_label="negative",
        )
    ]
    guidelines = [
        ContentGuideline(
            id="g1",
            created_at="2026-03-01",
            source_video_id="vid1",
            source_template_id="",
            guideline_type="avoid",
            rule="Don't use unclear timelines",
            evidence="Comments flagged inconsistency",
        )
    ]

    orch = FeedbackOrchestrator(
        fetcher=_make_fetcher(videos=videos, stats=stats, comments=raw_comments),
        sentiment_scorer=_make_scorer(scored=scored),
        guideline_generator=_make_generator(guidelines=guidelines),
        project_slug="test",
        project_root=tmp_path,
    )

    report = await orch.run_feedback_cycle()

    assert report.reels_analyzed == 1
    assert report.new_guidelines_count == 1
    assert len(report.flagged_reels) == 1

    # Check files were created
    feedback_dir = tmp_path / "projects" / "test" / "feedback" / "youtube"
    assert (feedback_dir / "reel_index.json").exists()
    assert (feedback_dir / "guidelines.yaml").exists()
    assert (feedback_dir / "comments" / "vid1.json").exists()

    # Verify reel_index content
    index_data = json.loads((feedback_dir / "reel_index.json").read_text())
    assert len(index_data) == 1
    assert index_data[0]["video_id"] == "vid1"


async def test_cycle_merges_with_existing_index(tmp_path: Path) -> None:
    # Pre-populate an existing index entry
    feedback_dir = tmp_path / "projects" / "test" / "feedback" / "youtube"
    feedback_dir.mkdir(parents=True)
    (feedback_dir / "comments").mkdir()

    existing = [{"reel_id": "old", "video_id": "old_vid", "title": "Old"}]
    (feedback_dir / "reel_index.json").write_text(json.dumps(existing))

    videos = [{"video_id": "new_vid", "title": "New", "description": "", "published_at": ""}]
    stats = [VideoMetrics(video_id="new_vid", view_count=500, like_count=40)]

    orch = FeedbackOrchestrator(
        fetcher=_make_fetcher(videos=videos, stats=stats),
        sentiment_scorer=_make_scorer(),
        guideline_generator=_make_generator(),
        project_slug="test",
        project_root=tmp_path,
    )
    await orch.run_feedback_cycle()

    index_data = json.loads((feedback_dir / "reel_index.json").read_text())
    video_ids = {e["video_id"] for e in index_data}
    assert "old_vid" in video_ids
    assert "new_vid" in video_ids
