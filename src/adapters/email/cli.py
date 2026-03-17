from __future__ import annotations

import asyncio
import logging
import re
from pathlib import Path

import typer
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .models import SendResult
from .sender import send_batch
from .settings import EmailSettings

app = typer.Typer(
    name="mmn-email",
    help="MarketMeNow email outreach CLI",
    no_args_is_help=True,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

console = Console()

_RANGE_RE = re.compile(r"^(\d+)-(\d+)$")


def _parse_range(value: str) -> tuple[int, int]:
    m = _RANGE_RE.match(value.strip())
    if not m:
        raise typer.BadParameter(
            f"Range must be START-END (e.g. 100-200), got: {value}"
        )
    start, end = int(m.group(1)), int(m.group(2))
    if start >= end:
        raise typer.BadParameter(
            f"Start ({start}) must be less than end ({end})"
        )
    return start, end


class _EmailProgress:
    """Live-updating terminal UI for the email send loop."""

    def __init__(self, live: Live, total: int, start: int) -> None:
        self._live = live
        self._total = total
        self._start = start
        self._entries: list[tuple[str, bool, str]] = []

    @property
    def succeeded(self) -> int:
        return sum(1 for _, ok, _ in self._entries if ok)

    @property
    def failed(self) -> int:
        return sum(1 for _, ok, _ in self._entries if not ok)

    def _render(self) -> Panel:
        tbl = Table(show_header=False, show_edge=False, pad_edge=False, box=None)
        tbl.add_column("status", width=3)
        tbl.add_column("info", ratio=1)

        visible = self._entries[-20:]
        for email, ok, err in visible:
            if ok:
                tbl.add_row("[bold green]✓[/bold green]", f"[green]{email}[/green]")
            else:
                tbl.add_row("[bold red]✗[/bold red]", f"[red]{email}[/red]  {err}")

        done = len(self._entries)
        progress = f"{done}/{self._total}  [green]{self.succeeded} sent[/green]"
        if self.failed:
            progress += f"  [red]{self.failed} failed[/red]"

        return Panel(
            tbl,
            title=f"[bold]Sending emails[/bold]  [dim]{progress}[/dim]",
            border_style="cyan" if done < self._total else "green",
        )

    def on_progress(
        self,
        current: int,
        total: int,
        email: str,
        success: bool,
        error: str,
    ) -> None:
        self._entries.append((email, success, error))
        self._live.update(self._render())


def _print_summary(results: list[SendResult], dry_run: bool) -> None:
    console.print()
    tbl = Table(title="Summary", show_header=False, border_style="bold")
    tbl.add_column("metric", style="bold")
    tbl.add_column("value", justify="right")

    succeeded = sum(1 for r in results if r.success)
    failed = sum(1 for r in results if not r.success)

    tbl.add_row("Mode", "[yellow]DRY RUN[/yellow]" if dry_run else "Live")
    tbl.add_row("Total", str(len(results)))
    tbl.add_row(
        "Sent",
        f"[green]{succeeded}[/green]" if succeeded else "0",
    )
    tbl.add_row(
        "Failed",
        f"[red]{failed}[/red]" if failed else "0",
    )
    console.print(tbl)

    if failed:
        console.print()
        err_tbl = Table(title="Failures", border_style="red")
        err_tbl.add_column("Row", style="dim", width=6)
        err_tbl.add_column("Email")
        err_tbl.add_column("Error", style="red")
        for r in results:
            if not r.success:
                err_tbl.add_row(str(r.row_index), r.email, r.error)
        console.print(err_tbl)


@app.command("send")
def send(
    csv_file: Path = typer.Option(
        ..., "-f", "--file",
        help="CSV file with contacts (must have an 'email' column)",
        exists=True, readable=True,
    ),
    template: Path = typer.Option(
        ..., "-t", "--template",
        help="HTML Jinja2 template file",
        exists=True, readable=True,
    ),
    subject: str = typer.Option(
        ..., "-s", "--subject",
        help="Email subject (supports Jinja2 placeholders from CSV columns)",
    ),
    row_range: str = typer.Option(
        ..., "-r", "--range",
        help="Row range as START-END (inclusive start, exclusive end, 0-indexed data rows)",
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run",
        help="Render emails and log them without actually sending",
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v",
        help="Show raw log output instead of rich UI",
    ),
) -> None:
    """Send templated emails to a slice of a CSV contact list.

    The CSV must have an 'email' column.  All other columns become
    Jinja2 template variables (usable in both the HTML template and
    the subject line).

    Every sent email is BCC'd to the sender address.

    Examples:

        mmn email send -f contacts.csv -t invite.html -s "Hey {{ name }}" -r 0-50

        mmn email send -f contacts.csv -t invite.html -s "Hello" -r 100-200 --dry-run
    """
    start, end = _parse_range(row_range)
    settings = EmailSettings()

    if not settings.smtp_username and not dry_run:
        console.print("[red]SMTP_USERNAME is not set in .env[/red]")
        raise typer.Exit(code=1)

    if dry_run:
        console.print("[yellow]DRY RUN — no emails will be sent[/yellow]")

    console.print(
        f"CSV [bold]{csv_file}[/bold]  rows [bold]{start}[/bold]–[bold]{end}[/bold]  "
        f"template [bold]{template.name}[/bold]"
    )

    async def _run() -> list[SendResult]:
        if verbose or dry_run:
            return await send_batch(
                settings, csv_file, template, subject, start, end,
                dry_run=dry_run,
            )

        from .sender import read_contacts
        total = len(read_contacts(csv_file, start, end))
        with Live(console=console, refresh_per_second=8, transient=False) as live:
            progress = _EmailProgress(live, total, start)
            return await send_batch(
                settings, csv_file, template, subject, start, end,
                dry_run=dry_run,
                on_progress=progress.on_progress,
            )

    results = asyncio.run(_run())
    _print_summary(results, dry_run)
