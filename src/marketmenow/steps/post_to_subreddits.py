from __future__ import annotations

import asyncio
import random

from marketmenow.core.workflow import WorkflowContext, WorkflowError


class PostToSubredditsStep:
    """Post generated content to multiple subreddits with delays between each."""

    @property
    def name(self) -> str:
        return "post-to-subreddits"

    @property
    def description(self) -> str:
        return "Post to Reddit subreddits with human-like delays"

    async def execute(self, ctx: WorkflowContext) -> None:
        from adapters.reddit.client import RedditClient
        from adapters.reddit.settings import RedditSettings

        posts = ctx.get_artifact("reddit_posts")
        if not posts:
            raise WorkflowError("No posts to submit (reddit_posts artifact is empty)")

        dry_run = bool(ctx.get_param("dry_run", False))

        if dry_run:
            ctx.console.print("[yellow]Dry run -- previewing posts:[/yellow]")
            for post in posts:
                ctx.console.print(f"\n[bold cyan]r/{post.subreddit}[/bold cyan]")
                ctx.console.print(f"[bold]{post.title}[/bold]")
                preview = post.body[:200] + "..." if len(post.body) > 200 else post.body
                ctx.console.print(f"[dim]{preview}[/dim]")
            ctx.set_artifact("post_results", [])
            return

        settings = RedditSettings()
        if not settings.reddit_session:
            raise WorkflowError("REDDIT_SESSION not set in .env")

        min_delay = int(ctx.get_param("min_delay", 120) or 120)
        max_delay = int(ctx.get_param("max_delay", 300) or 300)

        client = RedditClient(
            session_cookie=settings.reddit_session,
            username=settings.reddit_username,
            user_agent=settings.reddit_user_agent,
        )

        results = []
        async with client:
            if not await client.is_logged_in():
                raise WorkflowError("Reddit session is invalid or expired")

            for i, post in enumerate(posts):
                ctx.console.print(
                    f"  [cyan]Posting to r/{post.subreddit}[/cyan] ({i + 1}/{len(posts)})"
                )

                try:
                    resp = await client.submit_text_post(
                        subreddit=post.subreddit,
                        title=post.title,
                        text=post.body,
                    )
                    json_data = resp.get("json", {})
                    errors = json_data.get("errors", []) if isinstance(json_data, dict) else []

                    if errors:
                        ctx.console.print(f"  [red]r/{post.subreddit} failed: {errors}[/red]")
                        results.append(
                            {"subreddit": post.subreddit, "success": False, "error": str(errors)}
                        )
                    else:
                        data = json_data.get("data", {}) if isinstance(json_data, dict) else {}
                        url = data.get("url", "") if isinstance(data, dict) else ""
                        ctx.console.print(f"  [green]r/{post.subreddit} posted![/green] {url}")
                        results.append(
                            {"subreddit": post.subreddit, "success": True, "url": str(url)}
                        )
                except Exception as exc:
                    ctx.console.print(f"  [red]r/{post.subreddit} error: {exc}[/red]")
                    results.append(
                        {"subreddit": post.subreddit, "success": False, "error": str(exc)}
                    )

                if i < len(posts) - 1:
                    delay = random.uniform(min_delay, max_delay)
                    mins = int(delay) // 60
                    secs = int(delay) % 60
                    ctx.console.print(f"  [dim]Waiting {mins}m {secs}s before next post...[/dim]")
                    await asyncio.sleep(delay)

        succeeded = sum(1 for r in results if r["success"])
        ctx.console.print(f"\n[green]{succeeded}/{len(results)} posts published to Reddit[/green]")
        ctx.set_artifact("post_results", results)
