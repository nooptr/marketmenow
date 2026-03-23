from __future__ import annotations

from marketmenow.core.diversity_selector import select_diverse_examples


def test_select_diverse_empty_candidates() -> None:
    assert select_diverse_examples([], [], 3) == []


def test_select_diverse_fewer_than_n() -> None:
    items = ["a", "b"]
    embeddings = [[1.0, 0.0], [0.0, 1.0]]
    result = select_diverse_examples(items, embeddings, 5)
    assert result == ["a", "b"]


def test_select_diverse_picks_farthest() -> None:
    """With three vectors, seed=first, then pick the most distant."""
    items = ["close", "far", "medium"]
    embeddings = [
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.9, 0.1, 0.0],
    ]
    result = select_diverse_examples(items, embeddings, 2)
    assert result[0] == "close"
    assert result[1] == "far"


def test_select_diverse_fallback_on_empty_embeddings() -> None:
    """Candidates without embeddings are used as engagement-rank backfill."""
    items = ["has_emb", "no_emb_1", "no_emb_2"]
    embeddings = [[1.0, 0.0], [], []]
    result = select_diverse_examples(items, embeddings, 3)
    assert len(result) == 3
    assert result[0] == "has_emb"
    assert "no_emb_1" in result
    assert "no_emb_2" in result


def test_select_diverse_n_zero() -> None:
    result = select_diverse_examples(["a"], [[1.0]], 0)
    assert result == []


def test_select_diverse_identical_embeddings() -> None:
    """When all embeddings are identical, still returns n items."""
    items = ["a", "b", "c", "d"]
    emb = [1.0, 0.0]
    result = select_diverse_examples(items, [emb] * 4, 3)
    assert len(result) == 3
