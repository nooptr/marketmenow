from __future__ import annotations

from marketmenow.core.workflow import ParamDef, ParamType, Workflow
from marketmenow.steps.fetch_feedback import FetchYouTubeFeedbackStep
from marketmenow.steps.inject_reel_id import InjectReelIdStep
from marketmenow.steps.youtube_upload import YouTubeUploadStep

workflow = Workflow(
    name="youtube-short",
    description="Upload a local video as a YouTube Short with feedback-driven guidelines.",
    steps=(
        FetchYouTubeFeedbackStep(),
        InjectReelIdStep(),
        YouTubeUploadStep(),
    ),
    params=(
        ParamDef(
            name="video",
            type=ParamType.PATH,
            required=True,
            help="Path to the video file (MP4)",
        ),
        ParamDef(name="title", help="Video title"),
        ParamDef(name="description", help="Video description"),
        ParamDef(name="hashtags", help="Comma-separated hashtags"),
        ParamDef(name="privacy", help="Privacy status: public, unlisted, or private"),
        ParamDef(name="template", help="Template slug for reel ID tracking"),
        ParamDef(
            name="feedback_days",
            type=ParamType.INT,
            help="Number of days to look back for feedback (default: 7)",
        ),
    ),
)
