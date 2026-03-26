from __future__ import annotations

from marketmenow.core.workflow import ParamDef, ParamType, Workflow
from marketmenow.steps.discover_posts import DiscoverPostsStep
from marketmenow.steps.post_replies import PostRepliesStep

workflow = Workflow(
    name="facebook-engage",
    description="Discover posts in teacher Facebook groups, generate AI comments, and post them.",
    steps=(
        DiscoverPostsStep(platform="facebook"),
        PostRepliesStep(),
    ),
    params=(
        ParamDef(
            name="max_comments",
            type=ParamType.INT,
            default=0,
            help="Override max comments per day (0 = use settings default)",
        ),
        ParamDef(
            name="headless",
            type=ParamType.BOOL,
            default=True,
            help="Run browser in headless mode",
        ),
    ),
)
