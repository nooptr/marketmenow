from __future__ import annotations

from marketmenow.core.workflow import WorkflowContext, WorkflowError


class PostRepliesStep:
    """Post generated replies/comments via the engagement orchestrator.

    Reads ``generated_replies`` and ``engagement_orchestrator`` from context.
    """

    @property
    def name(self) -> str:
        return "post-replies"

    @property
    def description(self) -> str:
        return "Post generated replies/comments"

    async def execute(self, ctx: WorkflowContext) -> None:
        platform = str(ctx.artifacts.get("engagement_platform", ""))
        orchestrator = ctx.get_artifact("engagement_orchestrator")
        replies = ctx.get_artifact("generated_replies")

        if not replies:
            ctx.console.print("[yellow]No replies to post.[/yellow]")
            return

        if platform == "twitter":
            with ctx.console.status("[bold cyan]Posting Twitter replies..."):
                stats = await orchestrator.reply_from_list(replies)  # type: ignore[union-attr]
        elif platform == "reddit":
            with ctx.console.status("[bold cyan]Posting Reddit comments..."):
                stats = await orchestrator.comment_from_list(replies)  # type: ignore[union-attr]
        else:
            raise WorkflowError(f"Unsupported engagement platform: {platform}")

        ctx.console.print(
            f"[green]Engagement complete:[/green] "
            f"{stats.total_succeeded} succeeded, {stats.total_failed} failed"
        )
        ctx.set_artifact("engagement_stats", stats)
