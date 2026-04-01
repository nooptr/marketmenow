from __future__ import annotations

import asyncio
import logging
import random
from typing import TYPE_CHECKING

from google.genai.types import GenerateContentConfig
from jinja2 import Template

from marketmenow.integrations.genai import create_genai_client

from .discovery import DiscoveredPost
from .prompts import load_prompt

if TYPE_CHECKING:
    from marketmenow.models.project import BrandConfig, PersonaConfig

logger = logging.getLogger(__name__)

_MAX_RETRIES = 3
_INITIAL_BACKOFF_S = 5.0


class CommentGenerator:
    """Generates helpful, persona-driven Reddit comments using Gemini."""

    def __init__(
        self,
        gemini_model: str = "gemini-2.5-flash",
        mention_rate: int = 10,
        vertex_project: str = "",
        vertex_location: str = "us-central1",
        persona: PersonaConfig | None = None,
        brand: BrandConfig | None = None,
        project_slug: str | None = None,
    ) -> None:
        self._client = create_genai_client(
            vertex_project=vertex_project,
            vertex_location=vertex_location,
        )
        self._model = gemini_model
        self._mention_rate = mention_rate
        self._persona = persona
        self._brand = brand
        self._project_slug = project_slug

    async def generate_comment(
        self,
        post: DiscoveredPost,
        comment_number: int = 1,
    ) -> str:
        should_mention = random.randint(1, 100) <= self._mention_rate
        directive = (
            f"mention {self._brand.name} naturally — ALWAYS disclose your affiliation, "
            "never be salesy, lead with genuine help first"
            if should_mention and self._brand
            else "DO NOT mention any product. Just be genuinely helpful."
        )

        if self._persona and self._brand:
            from marketmenow.core.prompt_builder import PromptBuilder

            built = PromptBuilder().build(
                platform="reddit",
                function="comment",
                persona=self._persona,
                brand=self._brand,
                template_vars={
                    "subreddit": post.subreddit,
                    "post_title": post.post_title,
                    "post_text": post.post_text[:1500],
                    "comment_number": comment_number,
                    "should_mention": should_mention,
                    "mention_rate": self._mention_rate,
                    "directive": directive,
                    "author_handle": getattr(post, "author", "anonymous"),
                },
                project_slug=self._project_slug,
            )
            system_prompt = built.system
            user_prompt = built.user
        else:
            prompt_data = load_prompt("comment_generation")

            system_template = Template(prompt_data["system"])
            system_prompt = system_template.render(mention_rate=self._mention_rate)

            user_template = Template(prompt_data["user"])
            user_prompt = user_template.render(
                subreddit=post.subreddit,
                post_title=post.post_title,
                post_text=post.post_text[:1500],
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
                        "Gemini attempt %d/%d failed for r/%s post %s, retrying in %.0fs: %s",
                        attempt,
                        _MAX_RETRIES,
                        post.subreddit,
                        post.post_id,
                        backoff,
                        exc,
                    )
                    await asyncio.sleep(backoff)

        if comment_text is None:
            raise RuntimeError(
                f"All {_MAX_RETRIES} Gemini attempts failed for "
                f"r/{post.subreddit} post {post.post_id}"
            ) from last_exc

        logger.info(
            "Generated comment for r/%s post %s (mention=%s): %s",
            post.subreddit,
            post.post_id,
            should_mention,
            comment_text[:80],
        )
        return comment_text
