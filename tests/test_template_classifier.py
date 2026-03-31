from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from marketmenow.core.feedback.classifier import (
    TemplateCandidate,
    TemplateClassifier,
)


def _make_store(
    *,
    embeddings: list[list[float]] | None = None,
    cosine_distance: float = 0.1,
) -> MagicMock:
    store = MagicMock()
    store.embed_texts = AsyncMock(return_value=embeddings or [[0.1, 0.2, 0.3]])
    store.cosine_distance = MagicMock(return_value=cosine_distance)
    return store


async def test_classify_returns_best_match() -> None:
    store = MagicMock()
    # Templates get embeddings [1,0,0] and [0,1,0]
    store.embed_texts = AsyncMock(
        side_effect=[
            [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],  # template embeddings
            [[0.9, 0.1, 0.0]],  # query embedding (closer to first template)
        ]
    )
    # Return distances: 0.05 for first (similarity 0.95), 0.8 for second (similarity 0.2)
    store.cosine_distance = MagicMock(side_effect=[0.05, 0.8])

    classifier = TemplateClassifier(store)
    await classifier.precompute_template_embeddings(
        [
            TemplateCandidate(template_id="grade", name="Can AI Grade", text="grading demo"),
            TemplateCandidate(template_id="horror", name="Horror Story", text="reddit horror"),
        ]
    )

    result = await classifier.classify("Can AI grade this?", "Watch AI grade a paper")
    assert result.template_id == "grade"
    assert result.confidence == pytest.approx(0.95)
    assert result.is_confident is True


async def test_classify_below_threshold() -> None:
    store = _make_store(cosine_distance=0.5)  # similarity = 0.5 < 0.7
    classifier = TemplateClassifier(store)

    # Precompute with one template
    store.embed_texts = AsyncMock(
        side_effect=[
            [[0.1, 0.2, 0.3]],  # template
            [[0.9, 0.8, 0.7]],  # query
        ]
    )
    await classifier.precompute_template_embeddings(
        [
            TemplateCandidate(template_id="test", name="Test", text="test"),
        ]
    )

    result = await classifier.classify("Unrelated video", "About cooking")
    assert result.is_confident is False
    assert result.confidence == pytest.approx(0.5)


async def test_classify_no_templates() -> None:
    store = _make_store()
    classifier = TemplateClassifier(store)
    # Don't precompute
    result = await classifier.classify("Any video", "Description")
    assert result.template_id == "unknown"
    assert result.is_confident is False


async def test_classify_empty_embedding() -> None:
    store = MagicMock()
    store.embed_texts = AsyncMock(
        side_effect=[
            [[0.1, 0.2]],  # template
            [[]],  # empty query embedding
        ]
    )
    classifier = TemplateClassifier(store)
    await classifier.precompute_template_embeddings(
        [
            TemplateCandidate(template_id="test", name="Test", text="test"),
        ]
    )

    result = await classifier.classify("Video", "Desc")
    assert result.template_id == "unknown"
    assert result.is_confident is False
