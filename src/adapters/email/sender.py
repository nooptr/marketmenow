from __future__ import annotations

import csv
import logging
from email.message import EmailMessage
from pathlib import Path
from typing import Callable

import aiosmtplib
from jinja2 import BaseLoader, Environment

from .models import ContactRow, SendResult
from .settings import EmailSettings

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[int, int, str, bool, str], None]
"""(current_index, total, email, success, error) -- called after each send attempt."""


def read_contacts(
    csv_path: Path,
    start: int,
    end: int,
) -> list[tuple[int, ContactRow]]:
    """Read rows ``[start, end)`` from *csv_path* (0-indexed data rows, header excluded)."""
    contacts: list[tuple[int, ContactRow]] = []
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row_idx, row in enumerate(reader):
            if row_idx < start:
                continue
            if row_idx >= end:
                break
            email = row.get("email", "").strip()
            if not email:
                logger.warning("Row %d has no email — skipping", row_idx)
                continue
            fields = {k: v for k, v in row.items() if k != "email"}
            contacts.append((row_idx, ContactRow(email=email, fields=fields)))
    return contacts


def render_email(
    template_html: str,
    subject_template: str,
    variables: dict[str, str],
) -> tuple[str, str]:
    """Return ``(rendered_subject, rendered_html)``."""
    env = Environment(loader=BaseLoader(), autoescape=True)
    html = env.from_string(template_html).render(variables)
    subject = env.from_string(subject_template).render(variables)
    return subject, html


def _build_message(
    *,
    sender: str,
    to: str,
    subject: str,
    html_body: str,
    bcc: str,
) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = to
    msg["Subject"] = subject
    msg["Bcc"] = bcc
    msg.set_content(html_body, subtype="html")
    return msg


async def send_batch(
    settings: EmailSettings,
    csv_path: Path,
    template_path: Path,
    subject_template: str,
    start: int,
    end: int,
    *,
    dry_run: bool = False,
    on_progress: ProgressCallback | None = None,
) -> list[SendResult]:
    """Send emails to rows ``[start, end)`` of the CSV."""
    template_html = template_path.read_text(encoding="utf-8")
    contacts = read_contacts(csv_path, start, end)
    total = len(contacts)

    if total == 0:
        logger.info("No contacts in range [%d, %d)", start, end)
        return []

    results: list[SendResult] = []
    sender = settings.sender_address

    if dry_run:
        for i, (row_idx, contact) in enumerate(contacts, 1):
            subject, html = render_email(
                template_html, subject_template, contact.template_vars,
            )
            result = SendResult(row_index=row_idx, email=contact.email, success=True)
            results.append(result)
            if on_progress:
                on_progress(i, total, contact.email, True, "")
            logger.info(
                "[DRY RUN] Row %d → %s | Subject: %s", row_idx, contact.email, subject,
            )
        return results

    async with aiosmtplib.SMTP(
        hostname=settings.smtp_host,
        port=settings.smtp_port,
        use_tls=False,
        start_tls=settings.smtp_use_tls,
    ) as smtp:
        await smtp.login(settings.smtp_username, settings.smtp_password)

        for i, (row_idx, contact) in enumerate(contacts, 1):
            try:
                subject, html = render_email(
                    template_html, subject_template, contact.template_vars,
                )
                msg = _build_message(
                    sender=sender,
                    to=contact.email,
                    subject=subject,
                    html_body=html,
                    bcc=sender,
                )
                await smtp.send_message(msg)
                result = SendResult(row_index=row_idx, email=contact.email, success=True)
                logger.info("Row %d → %s  ✓", row_idx, contact.email)
            except Exception as exc:
                result = SendResult(
                    row_index=row_idx,
                    email=contact.email,
                    success=False,
                    error=str(exc),
                )
                logger.error("Row %d → %s  ✗ %s", row_idx, contact.email, exc)

            results.append(result)
            if on_progress:
                on_progress(i, total, contact.email, result.success, result.error)

    return results
