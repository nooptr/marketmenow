from __future__ import annotations

from marketmenow.core.workflow import WorkflowContext, WorkflowError


class DiscoverPostsStep:
    """Discover relevant posts on a social platform for engagement.

    Supports ``twitter`` and ``reddit``.
    """

    def __init__(self, platform: str) -> None:
        if platform not in ("twitter", "reddit"):
            raise ValueError(f"Unsupported discovery platform: {platform}")
        self._platform = platform

    @property
    def name(self) -> str:
        return f"discover-{self._platform}"

    @property
    def description(self) -> str:
        return f"Discover posts on {self._platform}"

    async def execute(self, ctx: WorkflowContext) -> None:
        if self._platform == "twitter":
            await self._discover_twitter(ctx)
        else:
            await self._discover_reddit(ctx)

    async def _discover_twitter(self, ctx: WorkflowContext) -> None:
        from adapters.twitter.orchestrator import EngagementOrchestrator
        from adapters.twitter.settings import TwitterSettings

        settings = TwitterSettings()
        headless = ctx.get_param("headless", True)
        if headless:
            settings = settings.model_copy(update={"headless": True})

        max_replies = int(ctx.get_param("max_replies", 0) or 0)
        if max_replies > 0:
            settings = settings.model_copy(update={"max_replies_per_day": max_replies})

        orchestrator = EngagementOrchestrator(settings)

        with ctx.console.status("[bold cyan]Discovering Twitter posts..."):
            posts = await orchestrator.discover_only()

        if not posts:
            raise WorkflowError("No posts discovered on Twitter. Are you logged in?")

        ctx.console.print(f"[green]Discovered {len(posts)} posts on Twitter[/green]")
        ctx.set_artifact("discovered_posts", posts)
        ctx.set_artifact("engagement_orchestrator", orchestrator)
        ctx.set_artifact("engagement_platform", "twitter")

    async def _discover_reddit(self, ctx: WorkflowContext) -> None:
        from adapters.reddit.orchestrator import EngagementOrchestrator
        from adapters.reddit.settings import RedditSettings

        settings = RedditSettings()
        max_comments = int(ctx.get_param("max_comments", 0) or 0)
        if max_comments > 0:
            settings = RedditSettings(
                **{**settings.model_dump(), "max_comments_per_day": max_comments},
            )

        orchestrator = EngagementOrchestrator(settings)

        with ctx.console.status("[bold cyan]Discovering Reddit posts..."):
            comments = await orchestrator.generate_only()

        if not comments:
            raise WorkflowError("No comments generated for Reddit.")

        ctx.console.print(f"[green]Generated {len(comments)} comments for Reddit[/green]")
        ctx.set_artifact("generated_replies", comments)
        ctx.set_artifact("engagement_orchestrator", orchestrator)
        ctx.set_artifact("engagement_platform", "reddit")
