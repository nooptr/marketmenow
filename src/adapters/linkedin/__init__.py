from __future__ import annotations

from marketmenow.registry import PlatformBundle

from .adapter import LinkedInAdapter
from .browser import LinkedInBrowser
from .renderer import LinkedInRenderer
from .settings import LinkedInSettings
from .uploader import LinkedInUploader


def create_linkedin_bundle(
    settings: LinkedInSettings | None = None,
) -> PlatformBundle:
    """Construct a fully-wired LinkedIn ``PlatformBundle``."""
    if settings is None:
        settings = LinkedInSettings()

    browser = LinkedInBrowser(
        session_path=settings.linkedin_session_path,
        user_data_dir=settings.linkedin_user_data_dir,
        headless=settings.headless,
        slow_mo_ms=settings.slow_mo_ms,
        proxy_url=settings.proxy_url,
        viewport_width=settings.viewport_width,
        viewport_height=settings.viewport_height,
    )

    return PlatformBundle(
        adapter=LinkedInAdapter(browser),
        renderer=LinkedInRenderer(),
        uploader=LinkedInUploader(),
    )


__all__ = [
    "LinkedInAdapter",
    "LinkedInBrowser",
    "LinkedInRenderer",
    "LinkedInSettings",
    "LinkedInUploader",
    "create_linkedin_bundle",
]
