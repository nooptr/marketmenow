from __future__ import annotations

import asyncio
import logging

from google import genai
from google.genai.types import GenerateContentConfig

from marketmenow.outreach.models import (
    CustomerProfile,
    OutreachMessage,
    ScoredProspect,
)

logger = logging.getLogger(__name__)

_MAX_RETRIES = 3
_INITIAL_BACKOFF_S = 5.0


class OutreachMessageGenerator:
    """Generates personalised outreach messages using Gemini. Platform-agnostic."""

    def __init__(
        self,
        gemini_model: str = "gemini-2.5-flash",
        vertex_project: str = "",
        vertex_location: str = "us-central1",
    ) -> None:
        self._client = genai.Client(
            vertexai=True,
            project=vertex_project,
            location=vertex_location,
        )
        self._model = gemini_model

    async def generate(
        self,
        prospect: ScoredProspect,
        customer_profile: CustomerProfile,
    ) -> OutreachMessage:
        from marketmenow.core.prompt_builder import PromptBuilder

        profile = prospect.user_profile
        ref_post_text = profile.triggering_posts[0] if profile.triggering_posts else ""
        ref_post_url = profile.triggering_post_urls[0] if profile.triggering_post_urls else ""

        built = PromptBuilder().build(
            platform="outreach",
            function="generate_message",
            template_vars={
                "product": customer_profile.product,
                "messaging": customer_profile.messaging,
                "handle": profile.handle,
                "bio": profile.bio,
                "dm_angle": prospect.dm_angle,
                "reference_post": customer_profile.messaging.reference_post,
                "triggering_post_text": ref_post_text,
                "triggering_post_url": ref_post_url,
            },
        )

        message_text = await self._call_gemini(built.system, built.user, profile.handle)

        return OutreachMessage(
            recipient_handle=profile.handle,
            message_text=message_text,
            referenced_post_url=ref_post_url,
            referenced_post_text=ref_post_text,
            prospect_score=prospect.total_score,
            dm_angle=prospect.dm_angle,
        )

    async def _call_gemini(
        self,
        system_prompt: str,
        user_prompt: str,
        handle: str,
    ) -> str:
        last_exc: BaseException | None = None

        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                response = await self._client.aio.models.generate_content(
                    model=self._model,
                    contents=user_prompt,
                    config=GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=1.0,
                    ),
                )
                text = (response.text or "").strip().strip('"').strip("'")
                if not text:
                    raise ValueError("Gemini returned empty response")
                return text
            except Exception as exc:
                last_exc = exc
                if attempt < _MAX_RETRIES:
                    backoff = _INITIAL_BACKOFF_S * (2 ** (attempt - 1))
                    logger.warning(
                        "MessageGen attempt %d/%d failed for @%s, retrying in %.0fs: %s",
                        attempt,
                        _MAX_RETRIES,
                        handle,
                        backoff,
                        exc,
                    )
                    await asyncio.sleep(backoff)

        raise RuntimeError(
            f"All {_MAX_RETRIES} Gemini message generation attempts failed for @{handle}"
        ) from last_exc
