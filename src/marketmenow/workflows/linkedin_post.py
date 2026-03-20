from __future__ import annotations

from marketmenow.core.workflow import ParamDef, ParamType, Workflow
from marketmenow.steps.linkedin_post import LinkedInPostStep

workflow = Workflow(
    name="linkedin-post",
    description="Generate AI-powered LinkedIn posts and publish them with human-like delays.",
    steps=(LinkedInPostStep(),),
    params=(
        ParamDef(
            name="count",
            short="-n",
            type=ParamType.INT,
            default=5,
            help="Number of posts to generate (1-20)",
        ),
        ParamDef(
            name="min_delay",
            type=ParamType.INT,
            default=300,
            help="Min delay between posts in seconds",
        ),
        ParamDef(
            name="max_delay",
            type=ParamType.INT,
            default=600,
            help="Max delay between posts in seconds",
        ),
        ParamDef(
            name="headless", type=ParamType.BOOL, default=False, help="Run browser in headless mode"
        ),
        ParamDef(
            name="dry_run",
            type=ParamType.BOOL,
            default=False,
            help="Generate posts without publishing",
        ),
    ),
)
