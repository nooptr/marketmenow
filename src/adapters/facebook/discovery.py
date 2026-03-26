from __future__ import annotations

import json
import logging
import random
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field

from .browser import FacebookBrowser

logger = logging.getLogger(__name__)


class DiscoveredGroupPost(BaseModel, frozen=True):
    group_url: str
    group_name: str
    post_url: str
    post_text: str
    post_author: str
    reactions_count: int = 0
    comments_count: int = 0
    discovered_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class GroupPostDiscoverer:
    """Finds posts in Facebook teacher groups via Playwright scraping."""

    def __init__(
        self,
        browser: FacebookBrowser,
        comment_history_path: Path,
    ) -> None:
        self._browser = browser
        self._history_path = comment_history_path
        self._commented_urls: set[str] = set()
        self._load_history()

    def _load_history(self) -> None:
        if self._history_path.exists():
            data = json.loads(self._history_path.read_text(encoding="utf-8"))
            self._commented_urls = set(data.get("commented_urls", []))
            logger.info(
                "Loaded %d previously commented post URLs",
                len(self._commented_urls),
            )

    def save_history(self) -> None:
        self._history_path.parent.mkdir(parents=True, exist_ok=True)
        self._history_path.write_text(
            json.dumps({"commented_urls": sorted(self._commented_urls)}, indent=2),
            encoding="utf-8",
        )

    def mark_commented(self, post_url: str) -> None:
        self._commented_urls.add(post_url)
        self.save_history()

    def already_commented(self, post_url: str) -> bool:
        return post_url in self._commented_urls

    async def discover_group_posts(
        self,
        group_url: str,
        group_name: str,
        max_posts: int = 5,
    ) -> list[DiscoveredGroupPost]:
        raw_posts = await self._browser.scrape_group_feed(group_url, max_posts=max_posts * 2)
        posts: list[DiscoveredGroupPost] = []
        for raw in raw_posts:
            post = DiscoveredGroupPost(
                group_url=group_url,
                group_name=group_name,
                post_url=raw["post_url"],
                post_text=raw["post_text"],
                post_author=raw.get("post_author", ""),
                reactions_count=int(raw.get("reactions", "0") or "0"),
                comments_count=int(raw.get("comments", "0") or "0"),
            )
            if self._is_eligible(post):
                posts.append(post)
        return posts[:max_posts]

    async def discover_all_groups(
        self,
        groups: list[dict[str, str]],
        max_per_group: int = 3,
    ) -> list[DiscoveredGroupPost]:
        """Discover posts across multiple groups.

        ``groups`` is a list of dicts with ``url`` and ``name`` keys.
        """
        all_posts: list[DiscoveredGroupPost] = []
        shuffled = list(groups)
        random.shuffle(shuffled)

        for group in shuffled:
            url = group["url"]
            name = group.get("name", url)
            try:
                posts = await self.discover_group_posts(url, name, max_posts=max_per_group)
                all_posts.extend(posts)
                logger.info("Discovered %d posts in %s", len(posts), name)
            except Exception:
                logger.exception("Failed to scrape group %s", name)

        return self._dedupe(all_posts)

    def _is_eligible(self, post: DiscoveredGroupPost) -> bool:
        if self.already_commented(post.post_url):
            return False
        if len(post.post_text.strip()) < 30:
            return False
        return True

    @staticmethod
    def _dedupe(posts: list[DiscoveredGroupPost]) -> list[DiscoveredGroupPost]:
        seen: set[str] = set()
        unique: list[DiscoveredGroupPost] = []
        for p in posts:
            if p.post_url not in seen:
                seen.add(p.post_url)
                unique.append(p)
        return unique
