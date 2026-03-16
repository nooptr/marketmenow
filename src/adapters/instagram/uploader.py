from __future__ import annotations

import shutil
from pathlib import Path
from uuid import uuid4

from marketmenow.models.content import MediaAsset
from marketmenow.models.result import MediaRef


class InstagramUploader:
    """Satisfies ``Uploader`` protocol.

    Copies local files into a publicly-servable directory and returns
    ``MediaRef`` objects.  In production this would upload to S3 / GCS
    and return presigned URLs.
    """

    def __init__(self, output_dir: Path) -> None:
        self._output_dir = output_dir / "uploads"
        self._output_dir.mkdir(parents=True, exist_ok=True)

    @property
    def platform_name(self) -> str:
        return "instagram"

    async def upload(self, asset: MediaAsset) -> MediaRef:
        src = Path(asset.uri)
        if not src.exists():
            return MediaRef(
                platform="instagram",
                remote_id="",
                remote_url=asset.uri,
            )

        dest_name = f"{uuid4().hex}{src.suffix}"
        dest = self._output_dir / dest_name
        shutil.copy2(src, dest)

        return MediaRef(
            platform="instagram",
            remote_id=dest_name,
            remote_url=str(dest.resolve()),
        )

    async def upload_batch(self, assets: list[MediaAsset]) -> list[MediaRef]:
        return [await self.upload(a) for a in assets]
