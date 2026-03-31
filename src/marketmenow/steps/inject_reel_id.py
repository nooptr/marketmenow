from __future__ import annotations

from marketmenow.core.reel_id import generate_reel_id, template_type_id_from_slug
from marketmenow.core.workflow import WorkflowContext


class InjectReelIdStep:
    """Inject discrete reel ID and template type ID into content metadata."""

    @property
    def name(self) -> str:
        return "inject-reel-id"

    @property
    def description(self) -> str:
        return "Embed reel tracking ID into video metadata"

    async def execute(self, ctx: WorkflowContext) -> None:
        content = ctx.artifacts.get("content")
        if content is None:
            # No content artifact yet — inject params for YouTubeUploadStep to use
            reel_id = generate_reel_id()
            template_slug = str(ctx.get_param("template", "") or "")
            tmpl_type = (
                template_type_id_from_slug(template_slug) if template_slug else generate_reel_id()
            )

            ctx.set_artifact("_reel_id_hex", reel_id.hex())
            ctx.set_artifact("_template_type_hex", tmpl_type.hex())
            return

        # Content exists (e.g., from GenerateReelStep) — inject into metadata
        reel_id = generate_reel_id()
        template_slug = str(ctx.get_param("template", "") or "")
        tmpl_type = (
            template_type_id_from_slug(template_slug) if template_slug else generate_reel_id()
        )

        new_meta = dict(content.metadata)
        new_meta["_reel_id_bytes"] = reel_id.hex()
        new_meta["_template_type_bytes"] = tmpl_type.hex()

        updated = content.model_copy(update={"metadata": new_meta})
        ctx.set_artifact("content", updated)
        ctx.set_artifact("_reel_id_hex", reel_id.hex())
        ctx.set_artifact("_template_type_hex", tmpl_type.hex())
