from __future__ import annotations

from marketmenow.registry import PlatformBundle

from .adapter import InstagramAdapter
from .renderer import InstagramRenderer
from .settings import InstagramSettings
from .uploader import InstagramUploader


def create_instagram_bundle(settings: InstagramSettings | None = None) -> PlatformBundle:
    """Construct a fully-wired Instagram ``PlatformBundle``."""
    if settings is None:
        settings = InstagramSettings()

    return PlatformBundle(
        adapter=InstagramAdapter(
            access_token=settings.instagram_access_token,
            business_account_id=settings.instagram_business_account_id,
        ),
        renderer=InstagramRenderer(),
        uploader=InstagramUploader(output_dir=settings.output_dir),
    )


__all__ = [
    "InstagramAdapter",
    "InstagramRenderer",
    "InstagramSettings",
    "InstagramUploader",
    "create_instagram_bundle",
]
