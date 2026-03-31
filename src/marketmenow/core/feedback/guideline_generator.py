from __future__ import annotations

import asyncio
import json
import logging
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from uuid import uuid4

from google.genai.types import GenerateContentConfig
from jinja2 import Template

from marketmenow.core.feedback.models import ContentGuideline, ReelIndexEntry
from marketmenow.integrations.genai import create_genai_client

logger = logging.getLogger(__name__)

_MAX_RETRIES = 3
_INITIAL_BACKOFF_S = 5.0
_PROMPTS_DIR = Path(__file__).resolve().parents[4] / "prompts" / "feedback"


@lru_cache(maxsize=4)
def _load_prompt(name: str) -> dict[str, str]:
    path = _PROMPTS_DIR / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Prompt '{name}' not found at {path}")
    import yaml

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return {"system": data.get("system", ""), "user": data.get("user", "")}


def should_generate_guidelines(entry: ReelIndexEntry) -> str | None:
    """Determine if a reel warrants guideline generation.

    Returns "avoid" for underperformers, "replicate" for top performers, None otherwise.
    """
    if not entry.metrics:
        return None

    view_count = entry.metrics.view_count
    like_count = entry.metrics.like_count
    like_ratio = like_count / max(view_count, 1) * 100

    # Underperformer signals
    if view_count < 250 or like_ratio < 2.0 or entry.avg_sentiment < 3.0:
        return "avoid"

    # Top performer signals
    if like_ratio > 8.0 or entry.avg_sentiment > 7.5:
        return "replicate"

    return None


class GuidelineGenerator:
    """Generates content guidelines from reel performance analysis using Gemini."""

    def __init__(
        self,
        gemini_model: str = "gemini-2.5-flash",
        vertex_project: str = "",
        vertex_location: str = "us-central1",
    ) -> None:
        self._client = create_genai_client(
            vertex_project=vertex_project,
            vertex_location=vertex_location,
        )
        self._model = gemini_model

    async def analyze_reel(
        self,
        entry: ReelIndexEntry,
        existing_guidelines: list[ContentGuideline],
    ) -> list[ContentGuideline]:
        """Analyze a reel and generate guidelines based on its performance."""
        if not entry.metrics:
            return []

        prompt_data = _load_prompt("generate_guidelines")
        system_prompt = prompt_data["system"]
        user_template = Template(prompt_data["user"])

        view_count = entry.metrics.view_count
        like_count = entry.metrics.like_count
        like_ratio = like_count / max(view_count, 1) * 100

        user_prompt = user_template.render(
            title=entry.title,
            template_id=entry.template_id,
            view_count=view_count,
            like_count=like_count,
            like_ratio=f"{like_ratio:.1f}",
            avg_sentiment=f"{entry.avg_sentiment:.1f}",
            comment_count=entry.metrics.comment_count,
            script=entry.script or "(script not available)",
            comments=entry.comments[:20],
            existing_guidelines=existing_guidelines,
        )

        raw_guidelines = await self._call_gemini(system_prompt, user_prompt)
        now = datetime.now(UTC).isoformat()

        guidelines: list[ContentGuideline] = []
        for item in raw_guidelines:
            guideline_type = str(item.get("guideline_type", "avoid"))
            if guideline_type not in ("avoid", "replicate"):
                guideline_type = "avoid"

            guidelines.append(
                ContentGuideline(
                    id=str(uuid4()),
                    created_at=now,
                    source_video_id=entry.video_id,
                    source_template_id=entry.template_id,
                    guideline_type=guideline_type,
                    rule=str(item.get("rule", "")),
                    evidence=str(item.get("evidence", "")),
                    metrics_snapshot=entry.metrics,
                )
            )

        return guidelines

    async def _call_gemini(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> list[dict[str, object]]:
        last_exc: BaseException | None = None

        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                response = await self._client.aio.models.generate_content(
                    model=self._model,
                    contents=user_prompt,
                    config=GenerateContentConfig(
                        system_instruction=system_prompt,
                        response_mime_type="application/json",
                        temperature=0.3,
                    ),
                )
                text = (response.text or "").strip()
                parsed = json.loads(text)
                if isinstance(parsed, dict):
                    return parsed.get("guidelines", [])  # type: ignore[no-any-return]
                if isinstance(parsed, list):
                    return parsed  # type: ignore[no-any-return]
                return []
            except Exception as exc:
                last_exc = exc
                if attempt < _MAX_RETRIES:
                    backoff = _INITIAL_BACKOFF_S * (2 ** (attempt - 1))
                    logger.warning(
                        "Guideline generation attempt %d/%d failed, retrying in %.0fs: %s",
                        attempt,
                        _MAX_RETRIES,
                        backoff,
                        exc,
                    )
                    await asyncio.sleep(backoff)

        raise RuntimeError(
            f"All {_MAX_RETRIES} guideline generation attempts failed"
        ) from last_exc
