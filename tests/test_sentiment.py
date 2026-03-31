from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

from marketmenow.core.feedback.sentiment import SentimentScorer


def _mock_genai_response(data: list[dict[str, object]]) -> MagicMock:
    response = MagicMock()
    response.text = json.dumps(data)
    return response


@patch("marketmenow.core.feedback.sentiment.create_genai_client")
async def test_score_comments_basic(mock_create_client: MagicMock) -> None:
    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(
        return_value=_mock_genai_response(
            [
                {
                    "comment_id": "c1",
                    "score": 8.5,
                    "label": "positive",
                    "reasoning": "Strong praise.",
                },
                {
                    "comment_id": "c2",
                    "score": 2.0,
                    "label": "negative",
                    "reasoning": "Disappointed.",
                },
            ]
        )
    )
    mock_create_client.return_value = mock_client

    scorer = SentimentScorer()
    comments = [
        {"comment_id": "c1", "author": "User1", "text": "Great!", "like_count": "5", "published_at": ""},
        {"comment_id": "c2", "author": "User2", "text": "Bad", "like_count": "0", "published_at": ""},
    ]
    results = await scorer.score_comments(comments, "Test Video")

    assert len(results) == 2
    assert results[0].sentiment_score == 8.5
    assert results[0].sentiment_label == "positive"
    assert results[0].author == "User1"
    assert results[1].sentiment_score == 2.0
    assert results[1].sentiment_label == "negative"


@patch("marketmenow.core.feedback.sentiment.create_genai_client")
async def test_score_comments_empty(mock_create_client: MagicMock) -> None:
    mock_create_client.return_value = MagicMock()
    scorer = SentimentScorer()
    results = await scorer.score_comments([], "Test")
    assert results == []


@patch("marketmenow.core.feedback.sentiment.create_genai_client")
async def test_score_clamps_to_range(mock_create_client: MagicMock) -> None:
    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(
        return_value=_mock_genai_response(
            [
                {"comment_id": "c1", "score": 15.0, "label": "positive", "reasoning": ""},
                {"comment_id": "c2", "score": -3.0, "label": "negative", "reasoning": ""},
            ]
        )
    )
    mock_create_client.return_value = mock_client

    scorer = SentimentScorer()
    comments = [
        {"comment_id": "c1", "author": "", "text": "", "like_count": "0", "published_at": ""},
        {"comment_id": "c2", "author": "", "text": "", "like_count": "0", "published_at": ""},
    ]
    results = await scorer.score_comments(comments, "Test")

    assert results[0].sentiment_score == 10.0
    assert results[1].sentiment_score == 0.0


@patch("marketmenow.core.feedback.sentiment.create_genai_client")
async def test_score_fixes_invalid_label(mock_create_client: MagicMock) -> None:
    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(
        return_value=_mock_genai_response(
            [{"comment_id": "c1", "score": 1.0, "label": "bad_label", "reasoning": ""}]
        )
    )
    mock_create_client.return_value = mock_client

    scorer = SentimentScorer()
    comments = [{"comment_id": "c1", "author": "", "text": "", "like_count": "0", "published_at": ""}]
    results = await scorer.score_comments(comments, "Test")
    assert results[0].sentiment_label == "negative"  # score 1.0 < 3.5
