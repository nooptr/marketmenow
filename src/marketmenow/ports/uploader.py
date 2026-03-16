from __future__ import annotations

from typing import Protocol, runtime_checkable

from marketmenow.models.content import MediaAsset
from marketmenow.models.result import MediaRef


@runtime_checkable
class Uploader(Protocol):
    @property
    def platform_name(self) -> str: ...

    async def upload(self, asset: MediaAsset) -> MediaRef: ...

    async def upload_batch(self, assets: list[MediaAsset]) -> list[MediaRef]: ...
