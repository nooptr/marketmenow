from __future__ import annotations

from pydantic import BaseModel, Field

from marketmenow.exceptions import UnsupportedModalityError
from marketmenow.models.content import (
    Article,
    BaseContent,
    ContentModality,
    DirectMessage,
    Document,
    ImagePost,
    MediaAsset,
    Poll,
    Reply,
    TextPost,
    Thread,
    VideoPost,
)


class NormalisedContent(BaseModel, frozen=True):
    """Platform-agnostic envelope that every adapter receives."""

    source: BaseContent
    modality: ContentModality
    text_segments: list[str]
    media_assets: list[MediaAsset]
    hashtags: list[str] = Field(default_factory=list)
    subject: str | None = None
    recipient_handles: list[str] = Field(default_factory=list)
    extra: dict[str, object] = Field(default_factory=dict)


class ContentNormaliser:
    """Converts any BaseContent subclass into a NormalisedContent envelope."""

    def normalise(self, content: BaseContent) -> NormalisedContent:
        match content:
            case VideoPost():
                return self._normalise_video(content)
            case ImagePost():
                return self._normalise_image(content)
            case Thread():
                return self._normalise_thread(content)
            case DirectMessage():
                return self._normalise_dm(content)
            case Reply():
                return self._normalise_reply(content)
            case TextPost():
                return self._normalise_text_post(content)
            case Document():
                return self._normalise_document(content)
            case Article():
                return self._normalise_article(content)
            case Poll():
                return self._normalise_poll(content)
            case _:
                raise UnsupportedModalityError(
                    platform="<core>",
                    modality=str(content.modality),
                )

    def _normalise_video(self, post: VideoPost) -> NormalisedContent:
        media: list[MediaAsset] = [post.video]
        if post.thumbnail is not None:
            media.append(post.thumbnail)

        return NormalisedContent(
            source=post,
            modality=ContentModality.VIDEO,
            text_segments=[post.caption] if post.caption else [],
            media_assets=media,
            hashtags=post.hashtags,
        )

    def _normalise_image(self, post: ImagePost) -> NormalisedContent:
        text_segments: list[str] = []
        if post.caption:
            text_segments.append(post.caption)

        return NormalisedContent(
            source=post,
            modality=ContentModality.IMAGE,
            text_segments=text_segments,
            media_assets=list(post.images),
            hashtags=post.hashtags,
        )

    def _normalise_thread(self, thread: Thread) -> NormalisedContent:
        text_segments = [entry.text for entry in thread.entries]
        media_assets: list[MediaAsset] = []
        for entry in thread.entries:
            media_assets.extend(entry.media)

        return NormalisedContent(
            source=thread,
            modality=ContentModality.THREAD,
            text_segments=text_segments,
            media_assets=media_assets,
        )

    def _normalise_dm(self, dm: DirectMessage) -> NormalisedContent:
        return NormalisedContent(
            source=dm,
            modality=ContentModality.DIRECT_MESSAGE,
            text_segments=[dm.body],
            media_assets=dm.attachments,
            subject=dm.subject,
            recipient_handles=[r.handle for r in dm.recipients],
        )

    def _normalise_reply(self, reply: Reply) -> NormalisedContent:
        return NormalisedContent(
            source=reply,
            modality=ContentModality.REPLY,
            text_segments=[reply.body],
            media_assets=list(reply.media),
            extra={
                "in_reply_to_url": reply.in_reply_to_url,
                "in_reply_to_platform_id": reply.in_reply_to_platform_id or "",
            },
        )

    def _normalise_text_post(self, post: TextPost) -> NormalisedContent:
        return NormalisedContent(
            source=post,
            modality=ContentModality.TEXT_POST,
            text_segments=[post.body] if post.body else [],
            media_assets=[],
            hashtags=post.hashtags,
        )

    def _normalise_document(self, doc: Document) -> NormalisedContent:
        text_segments: list[str] = []
        if doc.caption:
            text_segments.append(doc.caption)

        return NormalisedContent(
            source=doc,
            modality=ContentModality.DOCUMENT,
            text_segments=text_segments,
            media_assets=[doc.file],
            hashtags=doc.hashtags,
            extra={"document_title": doc.title},
        )

    def _normalise_article(self, article: Article) -> NormalisedContent:
        text_segments: list[str] = []
        if article.commentary:
            text_segments.append(article.commentary)

        return NormalisedContent(
            source=article,
            modality=ContentModality.ARTICLE,
            text_segments=text_segments,
            media_assets=[],
            hashtags=article.hashtags,
            extra={"article_url": article.url},
        )

    def _normalise_poll(self, poll: Poll) -> NormalisedContent:
        text_segments: list[str] = []
        if poll.commentary:
            text_segments.append(poll.commentary)

        return NormalisedContent(
            source=poll,
            modality=ContentModality.POLL,
            text_segments=text_segments,
            media_assets=[],
            hashtags=poll.hashtags,
            extra={
                "poll_question": poll.question,
                "poll_options": poll.options,
                "poll_duration_days": poll.duration_days,
            },
        )
