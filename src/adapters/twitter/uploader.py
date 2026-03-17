from __future__ import annotations

from marketmenow.models.content import MediaAsset
from marketmenow.models.result import MediaRef


class TwitterUploader:
    """Minimal uploader for Twitter/X -- replies are text-only for now."""

    @property
    def platform_name(self) -> str:
        return "twitter"

    async def upload(self, asset: MediaAsset) -> MediaRef:
        return MediaRef(
            platform="twitter",
            remote_id="",
            remote_url=asset.uri,
        )

    async def upload_batch(self, assets: list[MediaAsset]) -> list[MediaRef]:
        return [await self.upload(a) for a in assets]
