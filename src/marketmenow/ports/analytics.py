from __future__ import annotations

from typing import Protocol, runtime_checkable

from marketmenow.models.result import AnalyticsSnapshot, PublishResult


@runtime_checkable
class AnalyticsCollector(Protocol):
    @property
    def platform_name(self) -> str: ...

    async def collect(self, result: PublishResult) -> AnalyticsSnapshot: ...
