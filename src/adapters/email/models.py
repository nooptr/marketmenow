from __future__ import annotations

from pydantic import BaseModel, Field


class ContactRow(BaseModel, frozen=True):
    """A single row from the contacts CSV.

    The ``email`` field is required.  Every other column from the CSV
    is stored in ``fields`` and made available as Jinja2 template
    variables.
    """

    email: str
    fields: dict[str, str] = Field(default_factory=dict)

    @property
    def template_vars(self) -> dict[str, str]:
        """Merge ``email`` into the extra fields for template rendering."""
        return {"email": self.email, **self.fields}


class SendResult(BaseModel, frozen=True):
    row_index: int
    email: str
    success: bool
    error: str = ""
