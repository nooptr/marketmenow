from __future__ import annotations

from marketmenow.registry import PlatformBundle

from .adapter import TwitterAdapter
from .browser import StealthBrowser
from .renderer import TwitterRenderer
from .settings import TwitterSettings
from .uploader import TwitterUploader


def create_twitter_bundle(
    settings: TwitterSettings | None = None,
) -> PlatformBundle:
    """Construct a fully-wired Twitter/X ``PlatformBundle``."""
    if settings is None:
        settings = TwitterSettings()

    browser = StealthBrowser(
        session_path=settings.twitter_session_path,
        user_data_dir=settings.twitter_user_data_dir,
        headless=settings.headless,
        slow_mo_ms=settings.slow_mo_ms,
        proxy_url=settings.proxy_url,
        viewport_width=settings.viewport_width,
        viewport_height=settings.viewport_height,
    )

    return PlatformBundle(
        adapter=TwitterAdapter(
            browser,
            auth_token=settings.twitter_auth_token,
            ct0=settings.twitter_ct0,
        ),
        renderer=TwitterRenderer(),
        uploader=TwitterUploader(),
    )


__all__ = [
    "StealthBrowser",
    "TwitterAdapter",
    "TwitterRenderer",
    "TwitterSettings",
    "TwitterUploader",
    "create_twitter_bundle",
]
