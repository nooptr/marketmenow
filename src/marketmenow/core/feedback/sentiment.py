from __future__ import annotations

import asyncio
import json
import logging
from functools import lru_cache
from pathlib import Path

from google.genai.types import GenerateContentConfig
from jinja2 import Template

from marketmenow.core.feedback.models import CommentData
from marketmenow.integrations.genai import create_genai_client

logger = logging.getLogger(__name__)

_MAX_RETRIES = 3
_INITIAL_BACKOFF_S = 5.0
_BATCH_SIZE = 20
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


class SentimentScorer:
    """Scores YouTube comments on a 0-10 sentiment scale using Gemini."""

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

    async def score_comments(
        self,
        comments: list[dict[str, str]],
        video_title: str,
    ) -> list[CommentData]:
        """Score a list of comments and return CommentData objects."""
        if not comments:
            return []

        prompt_data = _load_prompt("score_sentiment")
        system_prompt = prompt_data["system"]
        user_template = Template(prompt_data["user"])

        results: list[CommentData] = []
        for i in range(0, len(comments), _BATCH_SIZE):
            batch = comments[i : i + _BATCH_SIZE]
            user_prompt = user_template.render(
                video_title=video_title,
                comments=batch,
            )
            scored = await self._call_gemini(system_prompt, user_prompt)
            for item in scored:
                score = max(0.0, min(10.0, float(item.get("score", 5.0))))
                label = str(item.get("label", "neutral"))
                if label not in ("negative", "neutral", "positive"):
                    if score < 3.5:
                        label = "negative"
                    elif score > 6.5:
                        label = "positive"
                    else:
                        label = "neutral"

                # Find matching comment to preserve original fields
                comment_id = str(item.get("comment_id", ""))
                original = next((c for c in batch if c.get("comment_id") == comment_id), None)

                results.append(
                    CommentData(
                        comment_id=comment_id,
                        author=original.get("author", "") if original else "",
                        text=original.get("text", "") if original else "",
                        like_count=int(original.get("like_count", 0)) if original else 0,
                        published_at=original.get("published_at", "") if original else "",
                        sentiment_score=score,
                        sentiment_label=label,
                    )
                )

        return results

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
                if isinstance(parsed, list):
                    return parsed  # type: ignore[no-any-return]
                return []
            except Exception as exc:
                last_exc = exc
                if attempt < _MAX_RETRIES:
                    backoff = _INITIAL_BACKOFF_S * (2 ** (attempt - 1))
                    logger.warning(
                        "Sentiment scoring attempt %d/%d failed, retrying in %.0fs: %s",
                        attempt,
                        _MAX_RETRIES,
                        backoff,
                        exc,
                    )
                    await asyncio.sleep(backoff)

        raise RuntimeError(
            f"All {_MAX_RETRIES} sentiment scoring attempts failed"
        ) from last_exc
