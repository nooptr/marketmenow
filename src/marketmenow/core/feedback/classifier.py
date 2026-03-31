from __future__ import annotations

import logging

from pydantic import BaseModel

from marketmenow.core.embedding_store import EmbeddingStore

logger = logging.getLogger(__name__)

_CONFIDENCE_THRESHOLD = 0.7


class TemplateCandidate(BaseModel, frozen=True):
    """A reel template available for classification."""

    template_id: str
    name: str
    text: str
    hashtags: list[str] = []


class ClassificationResult(BaseModel, frozen=True):
    """Result of classifying a video into a template category."""

    template_id: str
    confidence: float
    is_confident: bool


class TemplateClassifier:
    """Classifies YouTube videos into reel template categories using embeddings."""

    def __init__(self, embedding_store: EmbeddingStore) -> None:
        self._store = embedding_store
        self._template_embeddings: list[list[float]] = []
        self._template_ids: list[str] = []

    async def precompute_template_embeddings(
        self,
        templates: list[TemplateCandidate],
    ) -> None:
        """Embed all template texts. Call once before classifying videos."""
        texts = []
        self._template_ids = []
        for t in templates:
            hashtag_str = " ".join(f"#{h.lstrip('#')}" for h in t.hashtags)
            text = f"{t.name} | {t.text} | {hashtag_str}".strip()
            texts.append(text)
            self._template_ids.append(t.template_id)

        self._template_embeddings = await self._store.embed_texts(texts)

    async def classify(
        self,
        video_title: str,
        video_description: str,
    ) -> ClassificationResult:
        """Classify a video into the best-matching template."""
        if not self._template_embeddings:
            return ClassificationResult(
                template_id="unknown",
                confidence=0.0,
                is_confident=False,
            )

        query = f"{video_title} | {video_description}"
        embeddings = await self._store.embed_texts([query])
        if not embeddings or not embeddings[0]:
            return ClassificationResult(
                template_id="unknown",
                confidence=0.0,
                is_confident=False,
            )

        query_emb = embeddings[0]
        best_idx = -1
        best_similarity = -1.0

        for idx, tmpl_emb in enumerate(self._template_embeddings):
            if not tmpl_emb:
                continue
            distance = self._store.cosine_distance(query_emb, tmpl_emb)
            similarity = 1.0 - distance
            if similarity > best_similarity:
                best_similarity = similarity
                best_idx = idx

        if best_idx < 0:
            return ClassificationResult(
                template_id="unknown",
                confidence=0.0,
                is_confident=False,
            )

        return ClassificationResult(
            template_id=self._template_ids[best_idx],
            confidence=best_similarity,
            is_confident=best_similarity >= _CONFIDENCE_THRESHOLD,
        )
