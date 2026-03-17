from __future__ import annotations

import logging
import random

from google import genai
from google.genai.types import GenerateContentConfig
from jinja2 import Template
from pydantic import BaseModel

from .discovery import DiscoveredPost
from .prompts import load_prompt

logger = logging.getLogger(__name__)


class GradeasyContext(BaseModel, frozen=True):
    name: str = "Gradeasy"
    url: str = "gradeasy.ai"
    tagline: str = "AI-powered grading assistant for K-12 teachers"
    features: list[str] = [
        "Grades assignments against rubrics in seconds",
        "Supports images, PDFs, and handwritten work",
        "Saves teachers 8-15 hours per week",
        "Teachers keep full control over final grades",
        "Free to try",
    ]


class ReplyGenerator:
    """Generates witty, persona-driven replies using Gemini."""

    def __init__(
        self,
        gemini_model: str = "gemini-3-flash-preview",
        mention_rate: int = 45,
        vertex_project: str = "",
        vertex_location: str = "us-central1",
    ) -> None:
        self._client = genai.Client(
            vertexai=True,
            project=vertex_project,
            location=vertex_location,
        )
        self._model = gemini_model
        self._mention_rate = mention_rate
        self._context = GradeasyContext()

    async def generate_reply(
        self,
        post: DiscoveredPost,
        reply_number: int = 1,
    ) -> str:
        should_mention = random.randint(1, 100) <= self._mention_rate

        prompt_data = load_prompt("reply_generation")

        system_template = Template(prompt_data["system"])
        system_prompt = system_template.render(mention_rate=self._mention_rate)

        user_template = Template(prompt_data["user"])
        user_prompt = user_template.render(
            author_handle=post.author_handle,
            post_text=post.post_text[:500],
            reply_number=reply_number,
            should_mention=should_mention,
        )

        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=user_prompt,
            config=GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.9,
            ),
        )

        reply_text = (response.text or "").strip().strip('"').strip("'")

        logger.info(
            "Generated reply for @%s (mention=%s): %s",
            post.author_handle,
            should_mention,
            reply_text[:80],
        )
        return reply_text
