from __future__ import annotations

from marketmenow.core.workflow import ParamDef, ParamType, Workflow
from marketmenow.steps.generate_reddit_post import GenerateRedditPostStep
from marketmenow.steps.post_to_subreddits import PostToSubredditsStep

workflow = Workflow(
    name="reddit-launch",
    description="Generate and post product updates/milestones across multiple subreddits.",
    steps=(
        GenerateRedditPostStep(),
        PostToSubredditsStep(),
    ),
    params=(
        ParamDef(
            name="config",
            short="-c",
            type=ParamType.PATH,
            help="YAML config file with product info, subreddits, and settings",
        ),
        ParamDef(
            name="brief",
            short="-b",
            help="Raw content for the AI to adapt (inline text or path to a file)",
        ),
        ParamDef(
            name="product_name",
            help="Product name (overrides config)",
        ),
        ParamDef(
            name="product_description",
            help="One-line product description (overrides config)",
        ),
        ParamDef(
            name="subreddits",
            help="Comma-separated subreddits (overrides config)",
        ),
        ParamDef(
            name="post_type",
            help="Post type: update, milestone, or launch (overrides config)",
        ),
        ParamDef(
            name="product_url",
            help="Product URL",
        ),
        ParamDef(
            name="context",
            help="Additional context (e.g. what changed, milestone numbers)",
        ),
        ParamDef(
            name="min_delay",
            type=ParamType.INT,
            default=120,
            help="Min seconds between subreddit posts",
        ),
        ParamDef(
            name="max_delay",
            type=ParamType.INT,
            default=300,
            help="Max seconds between subreddit posts",
        ),
        ParamDef(
            name="dry_run",
            type=ParamType.BOOL,
            default=False,
            help="Generate posts without actually posting",
        ),
    ),
)
