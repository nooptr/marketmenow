from __future__ import annotations

from marketmenow.core.workflow import ParamDef, ParamType, Workflow
from marketmenow.steps.discover_posts import DiscoverPostsStep
from marketmenow.steps.generate_replies import GenerateRepliesStep
from marketmenow.steps.post_replies import PostRepliesStep

workflow = Workflow(
    name="twitter-engage",
    description="Discover posts, generate AI replies, and post them on Twitter/X.",
    steps=(
        DiscoverPostsStep(platform="twitter"),
        GenerateRepliesStep(),
        PostRepliesStep(),
    ),
    params=(
        ParamDef(
            name="max_replies",
            type=ParamType.INT,
            default=0,
            help="Override max replies (0 = use settings default)",
        ),
        ParamDef(
            name="headless",
            type=ParamType.BOOL,
            default=True,
            help="Run browser in headless mode",
        ),
    ),
)
