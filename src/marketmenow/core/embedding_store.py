from __future__ import annotations

import logging
import math

from marketmenow.integrations.genai import create_genai_client

logger = logging.getLogger(__name__)

_EMBEDDING_MODEL = "text-embedding-004"
_BATCH_SIZE = 100


class EmbeddingStore:
    """Thin wrapper around Gemini's embedding API with cosine distance math."""

    def __init__(
        self,
        *,
        vertex_project: str = "",
        vertex_location: str = "us-central1",
    ) -> None:
        self._client = create_genai_client(
            vertex_project=vertex_project,
            vertex_location=vertex_location,
        )

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Batch-embed *texts* via Gemini embedding model.

        Splits into chunks of ``_BATCH_SIZE`` to stay within API limits.
        Returns one embedding vector per input text.
        """
        all_embeddings: list[list[float]] = []
        for start in range(0, len(texts), _BATCH_SIZE):
            batch = texts[start : start + _BATCH_SIZE]
            try:
                response = await self._client.aio.models.embed_content(
                    model=_EMBEDDING_MODEL,
                    contents=batch,
                )
                for emb in response.embeddings:
                    all_embeddings.append(list(emb.values))
            except Exception:
                logger.warning(
                    "Embedding batch %d-%d failed, filling with empty vectors",
                    start,
                    start + len(batch),
                    exc_info=True,
                )
                all_embeddings.extend([] for _ in batch)
        return all_embeddings

    @staticmethod
    def cosine_distance(a: list[float], b: list[float]) -> float:
        """Return ``1 - cosine_similarity(a, b)``.

        Pure-stdlib math (no numpy). Returns 1.0 when either vector is empty.
        """
        if not a or not b or len(a) != len(b):
            return 1.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a == 0.0 or norm_b == 0.0:
            return 1.0
        return 1.0 - (dot / (norm_a * norm_b))
