from __future__ import annotations

from marketmenow.core.embedding_store import EmbeddingStore


def select_diverse_examples[T](
    candidates: list[T],
    embeddings: list[list[float]],
    n: int,
) -> list[T]:
    """Select *n* items from *candidates* that maximise embedding diversity.

    Uses **greedy farthest-point sampling**:

    1. Seed with the first candidate (assumed highest-engagement).
    2. At each step, pick the candidate whose *minimum* cosine distance
       to every already-selected item is largest.
    3. Candidates with empty embeddings are skipped during diversity
       selection and used as engagement-ranked backfill if needed.

    Returns up to *n* items.  If fewer than *n* candidates have valid
    embeddings the remaining slots are filled by positional order
    (engagement rank).
    """
    if n <= 0 or not candidates:
        return []
    if len(candidates) <= n:
        return list(candidates)

    has_emb: list[int] = [i for i, e in enumerate(embeddings) if e]
    no_emb: list[int] = [i for i, e in enumerate(embeddings) if not e]

    if len(has_emb) <= 1:
        return list(candidates[:n])

    selected_indices: list[int] = [has_emb[0]]
    remaining = set(has_emb[1:])

    while len(selected_indices) < n and remaining:
        best_idx = -1
        best_min_dist = -1.0

        for idx in remaining:
            min_dist = min(
                EmbeddingStore.cosine_distance(embeddings[idx], embeddings[sel])
                for sel in selected_indices
            )
            if min_dist > best_min_dist:
                best_min_dist = min_dist
                best_idx = idx

        if best_idx < 0:
            break
        selected_indices.append(best_idx)
        remaining.discard(best_idx)

    if len(selected_indices) < n:
        for idx in no_emb:
            if len(selected_indices) >= n:
                break
            if idx not in selected_indices:
                selected_indices.append(idx)

    return [candidates[i] for i in selected_indices]
