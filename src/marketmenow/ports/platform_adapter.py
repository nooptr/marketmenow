from __future__ import annotations

from typing import Protocol, runtime_checkable

from marketmenow.models.content import ContentModality
from marketmenow.models.result import PublishResult, SendResult
from marketmenow.normaliser import NormalisedContent


@runtime_checkable
class PlatformAdapter(Protocol):
    @property
    def platform_name(self) -> str: ...

    def supported_modalities(self) -> frozenset[ContentModality]: ...

    async def authenticate(self, credentials: dict[str, str]) -> None: ...

    async def publish(self, content: NormalisedContent) -> PublishResult: ...

    async def send_dm(self, content: NormalisedContent) -> SendResult: ...
