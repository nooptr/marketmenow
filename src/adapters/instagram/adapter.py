from __future__ import annotations

from datetime import datetime, timezone

import httpx

from marketmenow.models.content import ContentModality
from marketmenow.models.result import PublishResult, SendResult
from marketmenow.normaliser import NormalisedContent

_IG_GRAPH_BASE = "https://graph.facebook.com/v21.0"


class InstagramAdapter:
    """Instagram Graph API adapter satisfying ``PlatformAdapter`` protocol."""

    def __init__(self, access_token: str, business_account_id: str) -> None:
        self._token = access_token
        self._account_id = business_account_id
        self._client = httpx.AsyncClient(
            base_url=_IG_GRAPH_BASE,
            params={"access_token": self._token},
            timeout=60.0,
        )

    @property
    def platform_name(self) -> str:
        return "instagram"

    def supported_modalities(self) -> frozenset[ContentModality]:
        return frozenset({ContentModality.REEL, ContentModality.CAROUSEL})

    async def authenticate(self, credentials: dict[str, str]) -> None:
        resp = await self._client.get(f"/{self._account_id}", params={"fields": "id,username"})
        resp.raise_for_status()

    async def publish(self, content: NormalisedContent) -> PublishResult:
        media_refs: list[dict[str, str]] = content.extra.get("_media_refs", [])  # type: ignore[assignment]

        if content.modality == ContentModality.CAROUSEL:
            return await self._publish_carousel(content, media_refs)
        if content.modality == ContentModality.REEL:
            return await self._publish_reel(content, media_refs)

        return PublishResult(
            platform="instagram",
            success=False,
            error_message=f"Unsupported modality: {content.modality}",
        )

    async def send_dm(self, content: NormalisedContent) -> SendResult:
        return SendResult(
            platform="instagram",
            recipient_handle=content.recipient_handles[0] if content.recipient_handles else "",
            success=False,
            error_message="Instagram DMs via Graph API are not supported in this adapter",
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _publish_carousel(
        self, content: NormalisedContent, media_refs: list[dict[str, str]]
    ) -> PublishResult:
        child_ids: list[str] = []
        for ref in media_refs:
            url = ref.get("remote_url", "")
            resp = await self._client.post(
                f"/{self._account_id}/media",
                data={"image_url": url, "is_carousel_item": "true"},
            )
            resp.raise_for_status()
            child_ids.append(resp.json()["id"])

        caption = self._build_caption(content)
        resp = await self._client.post(
            f"/{self._account_id}/media",
            data={
                "media_type": "CAROUSEL",
                "caption": caption,
                "children": ",".join(child_ids),
            },
        )
        resp.raise_for_status()
        container_id = resp.json()["id"]

        return await self._await_and_publish(container_id)

    async def _publish_reel(
        self, content: NormalisedContent, media_refs: list[dict[str, str]]
    ) -> PublishResult:
        video_url = media_refs[0].get("remote_url", "") if media_refs else ""
        caption = self._build_caption(content)

        resp = await self._client.post(
            f"/{self._account_id}/media",
            data={
                "media_type": "REELS",
                "video_url": video_url,
                "caption": caption,
            },
        )
        resp.raise_for_status()
        container_id = resp.json()["id"]

        return await self._await_and_publish(container_id)

    async def _await_and_publish(self, container_id: str) -> PublishResult:
        import asyncio

        for _ in range(30):
            status_resp = await self._client.get(
                f"/{container_id}",
                params={"fields": "status_code"},
            )
            status_resp.raise_for_status()
            status = status_resp.json().get("status_code")
            if status == "FINISHED":
                break
            if status == "ERROR":
                return PublishResult(
                    platform="instagram",
                    success=False,
                    error_message=f"Container {container_id} failed processing",
                )
            await asyncio.sleep(2)

        resp = await self._client.post(
            f"/{self._account_id}/media_publish",
            data={"creation_id": container_id},
        )
        resp.raise_for_status()
        post_id = resp.json().get("id", "")

        return PublishResult(
            platform="instagram",
            success=True,
            remote_post_id=post_id,
            remote_url=f"https://www.instagram.com/p/{post_id}/",
            published_at=datetime.now(timezone.utc),
        )

    @staticmethod
    def _build_caption(content: NormalisedContent) -> str:
        parts: list[str] = list(content.text_segments)
        if content.hashtags:
            tag_line = " ".join(f"#{tag.lstrip('#')}" for tag in content.hashtags)
            parts.append(tag_line)
        caption = "\n\n".join(parts)
        return caption[:2200]
