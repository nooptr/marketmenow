from __future__ import annotations

from marketmenow.core.workflow import WorkflowContext, WorkflowError


class GenerateRepliesStep:
    """Generate AI replies/comments for discovered posts.

    For Twitter: reads ``engagement_orchestrator`` and calls ``generate_only()``.
    For Reddit: the discover step already generates comments, so this is a no-op.
    """

    @property
    def name(self) -> str:
        return "generate-replies"

    @property
    def description(self) -> str:
        return "Generate AI replies for discovered posts"

    async def execute(self, ctx: WorkflowContext) -> None:
        platform = str(ctx.artifacts.get("engagement_platform", ""))

        if platform == "reddit":
            if "generated_replies" in ctx.artifacts:
                return
            raise WorkflowError("Reddit discover step did not produce replies")

        if platform != "twitter":
            raise WorkflowError(f"Unsupported engagement platform: {platform}")

        orchestrator = ctx.get_artifact("engagement_orchestrator")

        with ctx.console.status("[bold cyan]Generating Twitter replies..."):
            replies = await orchestrator.generate_only()  # type: ignore[union-attr]

        if not replies:
            raise WorkflowError("No replies generated.")

        ctx.console.print(f"[green]Generated {len(replies)} replies[/green]")
        ctx.set_artifact("generated_replies", replies)
