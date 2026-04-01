from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path

from marketmenow.core.workflow import WorkflowContext

logger = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).resolve().parents[3] / "prompts" / "youtube"


@lru_cache(maxsize=4)
def _load_prompt(name: str) -> dict[str, str]:
    path = _PROMPTS_DIR / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Prompt '{name}' not found at {path}")
    import yaml

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return {"system": data.get("system", ""), "user": data.get("user", "")}


class PrepareYouTubeStep:
    """Generate YouTube-optimized title, description, and hashtags from reel content."""

    @property
    def name(self) -> str:
        return "prepare-youtube"

    @property
    def description(self) -> str:
        return "Generate YouTube title and description from reel content"

    async def execute(self, ctx: WorkflowContext) -> None:
        from google.genai.types import GenerateContentConfig

        from adapters.instagram.settings import InstagramSettings
        from marketmenow.integrations.genai import (
            configure_google_application_credentials,
            create_genai_client,
        )

        content = ctx.artifacts.get("content")
        if content is None:
            logger.warning("No content artifact found, skipping YouTube metadata generation")
            return

        # Extract script text from the content
        script = getattr(content, "caption", "") or ""
        if not script:
            text_segments = getattr(content, "text_segments", [])
            if text_segments:
                script = "\n".join(text_segments)

        brand_name = "Gradeasy"
        brand_url = "https://gradeasy.ai"
        if ctx.project and ctx.project.brand:
            brand_name = ctx.project.brand.name or brand_name
            brand_url = ctx.project.brand.url or brand_url

        template_type = str(ctx.get_param("template", "unknown"))

        prompt_data = _load_prompt("generate_metadata")
        system_prompt = prompt_data["system"]
        user_prompt = prompt_data["user"].format(
            script=script,
            brand_name=brand_name,
            brand_url=brand_url,
            template_type=template_type,
        )

        # Use Vertex AI credentials from Instagram settings (same as reel generation)
        ig_settings = InstagramSettings()
        configure_google_application_credentials(ig_settings.google_application_credentials)
        client = create_genai_client(
            vertex_project=ig_settings.vertex_ai_project,
            vertex_location=ig_settings.vertex_ai_location,
        )
        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_prompt,
            config=GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                temperature=0.8,
            ),
        )

        try:
            data = json.loads(response.text or "{}")
            yt_title = str(data.get("title", ""))[:100]
            raw_description = str(data.get("description", ""))
            yt_description = f"Check out {brand_name} at {brand_url}\n\n{raw_description}"
            yt_hashtags = str(data.get("hashtags", ""))

            ctx.set_artifact("_yt_title", yt_title)
            ctx.set_artifact("_yt_description", yt_description)
            ctx.set_artifact("_yt_hashtags", yt_hashtags)

            ctx.console.print(f"[cyan]YouTube title:[/cyan] {yt_title}")
        except (json.JSONDecodeError, Exception):
            logger.exception("Failed to parse YouTube metadata from Gemini")
            ctx.set_artifact("_yt_title", "")
            ctx.set_artifact("_yt_description", "")
            ctx.set_artifact("_yt_hashtags", "")
