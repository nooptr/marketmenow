from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class VideoMetrics(BaseModel, frozen=True):
    """YouTube video statistics snapshot."""

    video_id: str
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    collected_at: datetime | None = None


class CommentData(BaseModel, frozen=True):
    """A single YouTube comment with sentiment analysis."""

    comment_id: str
    author: str
    text: str
    like_count: int = 0
    published_at: str = ""
    sentiment_score: float = 5.0
    sentiment_label: str = "neutral"


class ReelIndexEntry(BaseModel, frozen=True):
    """An indexed reel with its metadata, metrics, and sentiment data."""

    reel_id: str
    video_id: str
    template_id: str = ""
    template_type_id: str = ""
    title: str = ""
    description: str = ""
    script: str = ""
    published_at: str = ""
    metrics: VideoMetrics | None = None
    comments: list[CommentData] = []
    avg_sentiment: float = 5.0


class ContentGuideline(BaseModel, frozen=True):
    """A permanent content guideline derived from reel performance analysis."""

    id: str
    created_at: str
    source_video_id: str
    source_template_id: str
    guideline_type: str  # "avoid" or "replicate"
    rule: str
    evidence: str
    metrics_snapshot: VideoMetrics | None = None


class GuidelinesFile(BaseModel, frozen=True):
    """Container for persisted guidelines."""

    guidelines: list[ContentGuideline] = []
    last_updated: str = ""


class FeedbackReport(BaseModel, frozen=True):
    """Summary of a feedback cycle run."""

    reels_analyzed: int = 0
    new_guidelines_count: int = 0
    avg_sentiment: float = 5.0
    flagged_reels: list[str] = []
