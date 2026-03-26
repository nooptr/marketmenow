from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from marketmenow.core.workflow import WorkflowContext, WorkflowError


class YouTubeUploadStep:
    """Upload a local video as a YouTube Short."""

    @property
    def name(self) -> str:
        return "youtube-upload"

    @property
    def description(self) -> str:
        return "Upload video to YouTube Shorts"

    async def execute(self, ctx: WorkflowContext) -> None:
        from adapters.youtube import create_youtube_bundle
        from adapters.youtube.settings import YouTubeSettings
        from marketmenow.core.pipeline import ContentPipeline
        from marketmenow.models.content import MediaAsset, VideoPost
        from marketmenow.registry import AdapterRegistry

        settings = YouTubeSettings()
        if not settings.youtube_refresh_token:
            raise WorkflowError("YOUTUBE_REFRESH_TOKEN not set. Run `mmn auth youtube` first.")

        video_path = Path(str(ctx.require_param("video")))
        if not video_path.exists():
            raise WorkflowError(f"Video file not found: {video_path}")

        title = str(ctx.get_param("title", "") or "")
        description = str(ctx.get_param("description", "") or "")
        hashtags_raw = str(ctx.get_param("hashtags", "") or "")
        tags = [t.strip() for t in hashtags_raw.split(",") if t.strip()]
        privacy = str(ctx.get_param("privacy", "") or "")

        caption_parts = [p for p in [title, description] if p]
        caption = "\n\n".join(caption_parts) if caption_parts else ""
        meta: dict[str, str] = {}
        if title:
            meta["_yt_title"] = title

        video_post = VideoPost(
            id=uuid4(),
            video=MediaAsset(uri=str(video_path.resolve()), mime_type="video/mp4"),
            caption=caption,
            hashtags=tags,
            metadata=meta,
        )

        bundle = create_youtube_bundle(settings)
        if privacy:
            bundle.adapter._default_privacy = privacy  # type: ignore[attr-defined]

        registry = AdapterRegistry()
        registry.register(bundle)
        pipeline = ContentPipeline(registry)

        with ctx.console.status("[bold blue]Uploading to YouTube Shorts..."):
            result = await pipeline.execute(video_post, "youtube")

        if hasattr(result, "success") and result.success:
            url = getattr(result, "remote_url", "") or ""
            ctx.console.print(f"[green]Published to YouTube![/green] {url}")
        else:
            err = getattr(result, "error_message", str(result))
            ctx.console.print(f"[red]YouTube upload failed:[/red] {err}")

        ctx.set_artifact("publish_result", result)
