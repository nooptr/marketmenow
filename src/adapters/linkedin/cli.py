from __future__ import annotations

import asyncio
import logging
import mimetypes
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from marketmenow.models.content import (
    Article,
    Document,
    ImagePost,
    MediaAsset,
    Poll,
    TextPost,
    VideoPost,
)
from marketmenow.normaliser import ContentNormaliser
from marketmenow.registry import AdapterRegistry

from . import create_linkedin_bundle
from .browser import LinkedInBrowser
from .settings import LinkedInSettings

app = typer.Typer(
    name="mmn-linkedin",
    help="MarketMeNow LinkedIn posting CLI",
    no_args_is_help=True,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)
console = Console()


def _settings() -> LinkedInSettings:
    return LinkedInSettings()


def _mime(path: Path) -> str:
    mime, _ = mimetypes.guess_type(str(path))
    return mime or "application/octet-stream"


def _make_browser(settings: LinkedInSettings) -> LinkedInBrowser:
    return LinkedInBrowser(
        session_path=settings.linkedin_session_path,
        user_data_dir=settings.linkedin_user_data_dir,
        headless=settings.headless,
        slow_mo_ms=settings.slow_mo_ms,
        proxy_url=settings.proxy_url,
        viewport_width=settings.viewport_width,
        viewport_height=settings.viewport_height,
    )


# ── Commands ─────────────────────────────────────────────────────────


@app.command()
def login(
    force: bool = typer.Option(
        False, "--force", help="Skip session check and log in fresh",
    ),
    cookies: bool = typer.Option(
        False, "--cookies", help="Log in by injecting li_at cookie",
    ),
) -> None:
    """Create a LinkedIn session for future commands.

    Two methods:

      mmn linkedin login --cookies    Inject li_at from your browser
                                      (set LINKEDIN_LI_AT in .env,
                                       or you'll be prompted).

      mmn linkedin login              Opens Chrome to linkedin.com --
                                      log in manually.
    """
    settings = _settings()

    async def _run() -> None:
        browser = _make_browser(settings)
        async with browser:
            if not force and not cookies:
                typer.echo("Checking existing session...")
                if await browser.is_logged_in():
                    typer.echo("Already logged in! Session is valid.")
                    return

            if cookies:
                li_at = settings.linkedin_li_at
                if not li_at:
                    li_at = typer.prompt("li_at cookie value")

                await browser.login_with_cookie(li_at)
                typer.echo("Cookie login successful. Session saved.")
            else:
                typer.echo(
                    "\nA browser window will open to linkedin.com.\n"
                    "Please log in manually (you have 5 minutes).\n"
                    "The session will be saved once you reach the feed.\n"
                )
                await browser.login_manual()
                typer.echo("Login successful. Session saved.")

    asyncio.run(_run())


@app.command()
def status() -> None:
    """Check LinkedIn login status."""
    settings = _settings()

    async def _run() -> bool:
        browser = _make_browser(settings)
        async with browser:
            return await browser.is_logged_in()

    table = Table(title="LinkedIn Status", show_header=False, border_style="bold")
    table.add_column("key", style="bold")
    table.add_column("value")

    table.add_row("Session file", str(settings.linkedin_session_path))
    table.add_row(
        "Session exists",
        "[green]yes[/green]" if settings.linkedin_session_path.exists() else "[red]no[/red]",
    )
    table.add_row(
        "li_at in .env",
        "[green]set[/green]" if settings.linkedin_li_at else "[dim]not set[/dim]",
    )

    console.print()
    console.print(table)
    console.print()


@app.command()
def post(
    text: Optional[str] = typer.Option(
        None, "--text", "-t", help="Post body text",
    ),
    image: Optional[list[Path]] = typer.Option(
        None, "--image", "-i", help="Image file(s) to attach",
        exists=True, readable=True,
    ),
    video: Optional[Path] = typer.Option(
        None, "--video", "-v", help="Video file to attach",
        exists=True, readable=True,
    ),
    document: Optional[Path] = typer.Option(
        None, "--document", "-d", help="Document file (PDF/PPT/DOCX) to attach",
        exists=True, readable=True,
    ),
    doc_title: Optional[str] = typer.Option(
        None, "--doc-title", help="Title for the document",
    ),
    article_url: Optional[str] = typer.Option(
        None, "--article", "-a", help="Article / link URL to share",
    ),
    poll_question: Optional[str] = typer.Option(
        None, "--poll", "-p", help="Poll question",
    ),
    poll_options: Optional[str] = typer.Option(
        None, "--poll-options", help="Comma-separated poll answers, 2-4 options",
    ),
    poll_days: int = typer.Option(
        3, "--poll-days", help="Poll duration in days (1-14)",
        min=1, max=14,
    ),
    hashtags: Optional[str] = typer.Option(
        None, "--hashtags", help="Comma-separated hashtags",
    ),
    headless: bool = typer.Option(
        False, "--headless", help="Run the browser in headless mode",
    ),
) -> None:
    """Publish a post to LinkedIn via the browser.

    Exactly one content type should be specified. If only --text is given,
    a text-only post is created. Combine --text with --image, --video,
    --document, --article, or --poll for rich content.
    """
    settings = _settings()
    if headless:
        settings = settings.model_copy(update={"headless": True})
    tag_list = [t.strip() for t in (hashtags or "").split(",") if t.strip()]

    content_flags = sum([
        bool(image),
        bool(video),
        bool(document),
        bool(article_url),
        bool(poll_question),
    ])
    if content_flags > 1:
        console.print("[red]Specify only one of --image, --video, --document, --article, or --poll.[/red]")
        raise typer.Exit(1)

    if not text and not image and not video and not document and not article_url and not poll_question:
        console.print("[red]Provide at least --text or a media/article/poll option.[/red]")
        raise typer.Exit(1)

    if poll_question and not poll_options:
        console.print("[red]--poll requires --poll-options (comma-separated, 2-4 choices).[/red]")
        raise typer.Exit(1)

    normaliser = ContentNormaliser()

    if image:
        assets = [
            MediaAsset(uri=str(p.resolve()), mime_type=_mime(p))
            for p in image
        ]
        model = ImagePost(images=assets, caption=text or "", hashtags=tag_list)
    elif video:
        asset = MediaAsset(uri=str(video.resolve()), mime_type=_mime(video))
        model = VideoPost(video=asset, caption=text or "", hashtags=tag_list)
    elif document:
        asset = MediaAsset(uri=str(document.resolve()), mime_type=_mime(document))
        model = Document(
            file=asset, title=doc_title or document.stem,
            caption=text or "", hashtags=tag_list,
        )
    elif article_url:
        model = Article(url=article_url, commentary=text or "", hashtags=tag_list)
    elif poll_question:
        choices = [o.strip() for o in (poll_options or "").split(",") if o.strip()]
        if len(choices) < 2 or len(choices) > 4:
            console.print("[red]Poll requires 2-4 options.[/red]")
            raise typer.Exit(1)
        model = Poll(
            question=poll_question, options=choices,
            duration_days=poll_days, commentary=text or "", hashtags=tag_list,
        )
    else:
        model = TextPost(body=text or "", hashtags=tag_list)

    normalised = normaliser.normalise(model)

    async def _run() -> None:
        bundle = create_linkedin_bundle(settings)
        browser: LinkedInBrowser = bundle.adapter._browser  # type: ignore[attr-defined]

        async with browser:
            if not await browser.is_logged_in():
                li_at = settings.linkedin_li_at
                if li_at:
                    await browser.login_with_cookie(li_at)
                else:
                    console.print(
                        "[red]Not logged in. Run `mmn linkedin login` first,[/red]\n"
                        "[red]or set LINKEDIN_LI_AT in .env.[/red]"
                    )
                    raise typer.Exit(1)

            rendered = await bundle.renderer.render(normalised)
            result = await bundle.adapter.publish(rendered)

            if result.success:
                console.print()
                console.print(Panel(
                    "[bold green]Published![/bold green]",
                    title="LinkedIn",
                    border_style="green",
                ))
            else:
                console.print()
                console.print(Panel(
                    f"[bold red]Publish failed[/bold red]\n\n"
                    f"Error: {result.error_message}",
                    title="LinkedIn",
                    border_style="red",
                ))
                raise typer.Exit(1)

    asyncio.run(_run())
