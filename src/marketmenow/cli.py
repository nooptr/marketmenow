from __future__ import annotations

import importlib.metadata

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from adapters.instagram.cli import app as instagram_app, reel_app, carousel_app
from adapters.twitter.cli import app as twitter_app

VERSION = importlib.metadata.version("marketmenow")

console = Console()

app = typer.Typer(
    name="mmn",
    invoke_without_command=True,
    no_args_is_help=False,
    rich_markup_mode="rich",
    help="Open-source agentic marketing framework.",
)

app.add_typer(
    instagram_app,
    name="instagram",
    help="Instagram content generation and publishing.",
    rich_help_panel="Platforms",
)
app.add_typer(
    twitter_app,
    name="twitter",
    help="Twitter/X engagement and reply automation.",
    rich_help_panel="Platforms",
)

app.add_typer(
    reel_app,
    name="reel",
    help="Reel generation (shortcut for instagram reel).",
    rich_help_panel="Shortcuts",
)
app.add_typer(
    carousel_app,
    name="carousel",
    help="Carousel generation (shortcut for instagram carousel).",
    rich_help_panel="Shortcuts",
)


def _banner() -> Panel:
    logo = Text()
    logo.append("  __  __ ", style="bold cyan")
    logo.append("            _        _   ", style="bold cyan")
    logo.append("\n")
    logo.append(" |  \\/  |", style="bold cyan")
    logo.append(" __ _ _ __| | _____| |_ ", style="bold cyan")
    logo.append("\n")
    logo.append(" | |\\/| |", style="bold cyan")
    logo.append("/ _` | '__| |/ / _ \\ __|", style="bold cyan")
    logo.append("\n")
    logo.append(" | |  | |", style="bold magenta")
    logo.append(" (_| | |  |   <  __/ |_ ", style="bold magenta")
    logo.append("\n")
    logo.append(" |_|  |_|", style="bold magenta")
    logo.append("\\__,_|_|  |_|\\_\\___|\\__|", style="bold magenta")
    logo.append("\n")
    logo.append("  __  __      _   _                   ", style="bold magenta")
    logo.append("\n")
    logo.append(" |  \\/  | ___| \\ | | _____      __", style="bold yellow")
    logo.append("\n")
    logo.append(" | |\\/| |/ _ \\  \\| |/ _ \\ \\ /\\ / /", style="bold yellow")
    logo.append("\n")
    logo.append(" | |  | |  __/ |\\  | (_) \\ V  V / ", style="bold yellow")
    logo.append("\n")
    logo.append(" |_|  |_|\\___|_| \\_|\\___/ \\_/\\_/  ", style="bold yellow")
    logo.append("\n\n", style="default")
    logo.append(f"  v{VERSION}", style="dim")
    logo.append("  |  ", style="dim")
    logo.append("Agentic Marketing Framework", style="italic")
    logo.append("  |  ", style="dim")
    logo.append("MIT License", style="dim green")

    return Panel(
        logo,
        border_style="bright_blue",
        padding=(1, 2),
    )


@app.callback()
def main(
    ctx: typer.Context,
) -> None:
    """Open-source agentic marketing framework.

    Automate content creation, publishing, and engagement across
    Instagram, Twitter/X, and more.
    """
    if ctx.invoked_subcommand is None:
        console.print(_banner())
        console.print()
        console.print(
            "  Run [bold cyan]mmn --help[/] to see available commands.\n"
        )


@app.command(rich_help_panel="Info")
def version() -> None:
    """Show the MarketMeNow version."""
    console.print(f"[bold]marketmenow[/bold] [cyan]{VERSION}[/cyan]")


@app.command(rich_help_panel="Info")
def platforms() -> None:
    """List all supported platforms and their content modalities."""
    table = Table(
        title="Platform Support",
        title_style="bold",
        show_lines=True,
        padding=(0, 2),
    )
    table.add_column("Platform", style="bold cyan", min_width=16)
    table.add_column("Status", min_width=14)
    table.add_column("Modalities", min_width=30)
    table.add_column("Entry Point", style="dim", min_width=18)

    table.add_row(
        "Instagram",
        "[green]Implemented[/]",
        "Reels, Carousels",
        "mmn instagram",
    )
    table.add_row(
        "X / Twitter",
        "[green]Implemented[/]",
        "Replies, Threads",
        "mmn twitter",
    )
    table.add_row("Facebook", "[yellow]Planned[/]", "Reels, Carousels, DMs", "")
    table.add_row("LinkedIn", "[yellow]Planned[/]", "Threads, Carousels", "")
    table.add_row("TikTok", "[yellow]Planned[/]", "Reels", "")
    table.add_row("YouTube Shorts", "[yellow]Planned[/]", "Reels", "")
    table.add_row("Gmail / Email", "[yellow]Planned[/]", "Direct Messages", "")
    table.add_row("Threads (Meta)", "[yellow]Planned[/]", "Threads", "")
    table.add_row("Pinterest", "[yellow]Planned[/]", "Carousels", "")
    table.add_row("Bluesky", "[yellow]Planned[/]", "Threads", "")
    table.add_row("Reddit", "[yellow]Planned[/]", "Threads, Replies", "")
    table.add_row("WhatsApp Business", "[yellow]Planned[/]", "Direct Messages", "")

    console.print()
    console.print(table)
    console.print()


if __name__ == "__main__":
    app()
