from __future__ import annotations

from marketmenow.core.workflow import ParamDef, ParamType, Workflow
from marketmenow.steps.send_emails import SendEmailsStep

workflow = Workflow(
    name="email-outreach",
    description="Send templated emails to a CSV contact list or single recipient.",
    steps=(SendEmailsStep(),),
    params=(
        ParamDef(
            name="template",
            short="-t",
            type=ParamType.PATH,
            required=True,
            help="HTML Jinja2 template file",
        ),
        ParamDef(name="to", help="Single recipient email address"),
        ParamDef(
            name="vars", help="Template variables as key=value (comma-separated, used with --to)"
        ),
        ParamDef(
            name="csv_file",
            short="-f",
            type=ParamType.PATH,
            help="CSV file with contacts (must have 'email' column)",
        ),
        ParamDef(name="subject", short="-s", help="Email subject (supports Jinja2 placeholders)"),
        ParamDef(name="range", short="-r", help="Row range as START-END (0-indexed)"),
        ParamDef(
            name="paraphrase",
            type=ParamType.BOOL,
            default=False,
            help="Rewrite each email uniquely via Gemini",
        ),
        ParamDef(
            name="dry_run", type=ParamType.BOOL, default=False, help="Render emails without sending"
        ),
    ),
)
