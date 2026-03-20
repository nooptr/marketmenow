from __future__ import annotations

from marketmenow.core.workflow import ParamDef, ParamType, Workflow
from marketmenow.steps.discover_posts import DiscoverPostsStep
from marketmenow.steps.post_replies import PostRepliesStep

workflow = Workflow(
    name="reddit-engage",
    description="Discover posts, generate AI comments, and post them on Reddit.",
    steps=(
        DiscoverPostsStep(platform="reddit"),
        PostRepliesStep(),
    ),
    params=(
        ParamDef(
            name="max_comments",
            type=ParamType.INT,
            default=0,
            help="Override max comments per day (0 = use settings default)",
        ),
    ),
)
