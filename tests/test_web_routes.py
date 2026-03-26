"""Tests for web route handlers with mocked database.

These tests verify the FastAPI routes respond correctly without needing
a running PostgreSQL instance. All ``web.db`` calls are monkeypatched.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_content_item(**overrides: object) -> dict:
    defaults: dict[str, object] = {
        "id": uuid.uuid4(),
        "platform": "instagram",
        "modality": "video",
        "title": "Test reel",
        "status": "pending_review",
        "generate_command": ["mmn", "reel", "create"],
        "publish_command": ["mmn", "reel", "create", "--publish"],
        "preview_data": {},
        "progress_data": {},
        "output_path": None,
        "error_message": None,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }
    defaults.update(overrides)
    return defaults


def _make_record(data: dict) -> dict:
    """Simulate an asyncpg Record (dict-like)."""
    return data


@pytest.fixture
def mock_db(monkeypatch: pytest.MonkeyPatch):
    """Patch web.db functions so routes don't need a real database."""
    import web.db as db_module

    sample_item = _make_content_item()

    monkeypatch.setattr(db_module, "init_pool", AsyncMock(return_value=None))
    monkeypatch.setattr(db_module, "close_pool", AsyncMock(return_value=None))
    monkeypatch.setattr(
        db_module,
        "list_content_items",
        AsyncMock(return_value=[_make_record(sample_item)]),
    )
    monkeypatch.setattr(
        db_module,
        "get_platform_activity_stats",
        AsyncMock(return_value=[]),
    )
    monkeypatch.setattr(
        db_module,
        "get_content_item",
        AsyncMock(return_value=_make_record(sample_item)),
    )
    monkeypatch.setattr(
        db_module,
        "insert_content_item",
        AsyncMock(return_value=sample_item["id"]),
    )
    monkeypatch.setattr(
        db_module, "update_content_status", AsyncMock(return_value=None)
    )
    monkeypatch.setattr(db_module, "update_progress_data", AsyncMock(return_value=None))
    monkeypatch.setattr(
        db_module,
        "enqueue_content",
        AsyncMock(return_value=uuid.uuid4()),
    )
    monkeypatch.setattr(
        db_module,
        "list_queue_items",
        AsyncMock(return_value=[]),
    )
    monkeypatch.setattr(
        db_module,
        "get_rate_limits",
        AsyncMock(return_value=[]),
    )
    monkeypatch.setattr(
        db_module,
        "get_post_log",
        AsyncMock(return_value=[]),
    )
    monkeypatch.setattr(
        db_module,
        "clear_all_content",
        AsyncMock(return_value=0),
    )
    monkeypatch.setattr(
        db_module,
        "list_history_items",
        AsyncMock(return_value=[]),
    )

    return sample_item


@pytest.fixture
def client(mock_db: dict) -> TestClient:
    """Create a TestClient with mocked DB and disabled background tasks."""
    from contextlib import asynccontextmanager

    from fastapi import FastAPI
    from fastapi.staticfiles import StaticFiles

    from web.deps import STATIC_DIR
    from web.routes.dashboard import router as dashboard_router
    from web.routes.generate import router as generate_router
    from web.routes.queue import router as queue_router
    from web.routes.review import router as review_router

    @asynccontextmanager
    async def noop_lifespan(_app: FastAPI):
        yield

    test_app = FastAPI(lifespan=noop_lifespan)
    test_app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    test_app.include_router(dashboard_router)
    test_app.include_router(generate_router)
    test_app.include_router(review_router)
    test_app.include_router(queue_router)

    return TestClient(test_app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Dashboard routes
# ---------------------------------------------------------------------------


class TestDashboard:
    def test_dashboard_returns_200(self, client: TestClient) -> None:
        resp = client.get("/")
        assert resp.status_code == 200
        assert "MarketMeNow" in resp.text or "Dashboard" in resp.text

    def test_dashboard_with_status_filter(self, client: TestClient) -> None:
        resp = client.get("/?status=pending_review")
        assert resp.status_code == 200

    def test_dashboard_with_platform_filter(self, client: TestClient) -> None:
        resp = client.get("/?platform=instagram")
        assert resp.status_code == 200

    def test_history_returns_200(self, client: TestClient) -> None:
        resp = client.get("/history")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Generate routes
# ---------------------------------------------------------------------------


class TestGenerate:
    def test_generate_page_returns_200(self, client: TestClient) -> None:
        resp = client.get("/generate")
        assert resp.status_code == 200

    def test_generate_page_contains_platforms(self, client: TestClient) -> None:
        resp = client.get("/generate")
        assert "instagram" in resp.text.lower() or "Instagram" in resp.text

    def test_generate_unknown_platform_returns_error(self, client: TestClient) -> None:
        resp = client.post(
            "/generate",
            data={"platform": "nonexistent", "command_type": "nope"},
        )
        assert resp.status_code == 200
        assert "Unknown command" in resp.text or "error" in resp.text.lower()


# ---------------------------------------------------------------------------
# Queue routes
# ---------------------------------------------------------------------------


class TestQueues:
    def test_queues_page_returns_200(self, client: TestClient) -> None:
        resp = client.get("/queues")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Review routes
# ---------------------------------------------------------------------------


class TestReview:
    def test_approve_returns_200(self, client: TestClient, mock_db: dict) -> None:
        item_id = mock_db["id"]
        resp = client.post(f"/content/{item_id}/approve")
        assert resp.status_code == 200

    def test_reject_returns_200(self, client: TestClient, mock_db: dict) -> None:
        item_id = mock_db["id"]
        resp = client.post(f"/content/{item_id}/reject")
        assert resp.status_code == 200
