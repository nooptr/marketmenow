from __future__ import annotations

import asyncio
import logging
import random

from google.genai.types import GenerateContentConfig
from jinja2 import Template

from marketmenow.integrations.genai import create_genai_client

from .discovery import DiscoveredGroupPost
from .prompts import load_prompt

logger = logging.getLogger(__name__)

_MAX_RETRIES = 3
_INITIAL_BACKOFF_S = 5.0


class CommentGenerator:
    """Generates helpful, persona-driven Facebook group comments using Gemini."""

    def __init__(
        self,
        gemini_model: str = "gemini-2.5-flash",
        mention_rate: int = 10,
        vertex_project: str = "",
        vertex_location: str = "us-central1",
        project_slug: str | None = None,
    ) -> None:
        self._client = create_genai_client(
            vertex_project=vertex_project,
            vertex_location=vertex_location,
        )
        self._model = gemini_model
        self._mention_rate = mention_rate
        self._project_slug = project_slug

    async def generate_comment(
        self,
        post: DiscoveredGroupPost,
        comment_number: int = 1,
    ) -> str:
        should_mention = random.randint(1, 100) <= self._mention_rate

        prompt_data = load_prompt("comment_generation", project_slug=self._project_slug)

        system_template = Template(prompt_data["system"])
        system_prompt = system_template.render(mention_rate=self._mention_rate)

        user_template = Template(prompt_data["user"])
        user_prompt = user_template.render(
            group_name=post.group_name,
            post_author=post.post_author,
            post_text=post.post_text[:2000],
            comment_number=comment_number,
            should_mention=should_mention,
        )

        comment_text: str | None = None
        last_exc: BaseException | None = None

        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                response = await self._client.aio.models.generate_content(
                    model=self._model,
                    contents=user_prompt,
                    config=GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=0.9,
                    ),
                )
                comment_text = (response.text or "").strip().strip('"').strip("'")
                break
            except Exception as exc:
                last_exc = exc
                if attempt < _MAX_RETRIES:
                    backoff = _INITIAL_BACKOFF_S * (2 ** (attempt - 1))
                    logger.warning(
                        "Gemini attempt %d/%d failed for group %s, retrying in %.0fs: %s",
                        attempt,
                        _MAX_RETRIES,
                        post.group_name,
                        backoff,
                        exc,
                    )
                    await asyncio.sleep(backoff)

        if comment_text is None:
            raise RuntimeError(
                f"All {_MAX_RETRIES} Gemini attempts failed for "
                f"group {post.group_name} post {post.post_url}"
            ) from last_exc

        logger.info(
            "Generated comment for %s (mention=%s): %s",
            post.group_name,
            should_mention,
            comment_text[:80],
        )
        return comment_text
