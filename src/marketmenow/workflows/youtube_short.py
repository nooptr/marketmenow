from __future__ import annotations

from marketmenow.core.workflow import ParamDef, ParamType, Workflow
from marketmenow.steps.youtube_upload import YouTubeUploadStep

workflow = Workflow(
    name="youtube-short",
    description="Upload a local video as a YouTube Short.",
    steps=(YouTubeUploadStep(),),
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
    ),
)
