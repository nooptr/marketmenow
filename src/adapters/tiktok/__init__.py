from __future__ import annotations

from marketmenow.registry import PlatformBundle

from .adapter import TikTokAdapter
from .renderer import TikTokRenderer
from .settings import TikTokSettings
from .uploader import TikTokUploader


def create_tiktok_bundle(
    settings: TikTokSettings | None = None,
) -> PlatformBundle:
    """Construct a fully-wired TikTok ``PlatformBundle``."""
    if settings is None:
        settings = TikTokSettings()

    return PlatformBundle(
        adapter=TikTokAdapter(
            client_key=settings.tiktok_client_key,
            client_secret=settings.tiktok_client_secret,
            access_token=settings.tiktok_access_token,
            refresh_token=settings.tiktok_refresh_token,
            default_privacy=settings.tiktok_default_privacy,
            session_id=settings.tiktok_session_id,
            session_path=str(settings.tiktok_session_path),
            user_data_dir=str(settings.tiktok_user_data_dir),
            headless=settings.headless,
            slow_mo_ms=settings.slow_mo_ms,
            proxy_url=settings.proxy_url,
            viewport_width=settings.viewport_width,
            viewport_height=settings.viewport_height,
        ),
        renderer=TikTokRenderer(),
        uploader=TikTokUploader(),
    )


__all__ = [
    "TikTokAdapter",
    "TikTokRenderer",
    "TikTokSettings",
    "TikTokUploader",
    "create_tiktok_bundle",
]
