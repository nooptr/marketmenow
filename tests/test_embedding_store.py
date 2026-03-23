from __future__ import annotations

import math

from marketmenow.core.embedding_store import EmbeddingStore


def test_cosine_distance_identical() -> None:
    a = [1.0, 0.0, 0.0]
    assert EmbeddingStore.cosine_distance(a, a) == 0.0


def test_cosine_distance_orthogonal() -> None:
    a = [1.0, 0.0]
    b = [0.0, 1.0]
    assert math.isclose(EmbeddingStore.cosine_distance(a, b), 1.0)


def test_cosine_distance_opposite() -> None:
    a = [1.0, 0.0]
    b = [-1.0, 0.0]
    assert math.isclose(EmbeddingStore.cosine_distance(a, b), 2.0)


def test_cosine_distance_empty_vectors() -> None:
    assert EmbeddingStore.cosine_distance([], [1.0]) == 1.0
    assert EmbeddingStore.cosine_distance([1.0], []) == 1.0
    assert EmbeddingStore.cosine_distance([], []) == 1.0


def test_cosine_distance_mismatched_lengths() -> None:
    assert EmbeddingStore.cosine_distance([1.0], [1.0, 2.0]) == 1.0


def test_cosine_distance_zero_vector() -> None:
    assert EmbeddingStore.cosine_distance([0.0, 0.0], [1.0, 0.0]) == 1.0


def test_cosine_distance_partial_overlap() -> None:
    a = [1.0, 1.0]
    b = [1.0, 0.0]
    dist = EmbeddingStore.cosine_distance(a, b)
    expected = 1.0 - (1.0 / (math.sqrt(2) * 1.0))
    assert math.isclose(dist, expected, rel_tol=1e-9)
