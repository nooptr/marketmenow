from __future__ import annotations

import asyncio
import json
import logging
import random
from pathlib import Path

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
)
from playwright_stealth import Stealth

logger = logging.getLogger(__name__)

_TWITTER_HOME = "https://x.com/home"
_TWITTER_BASE = "https://x.com"


class StealthBrowser:
    """Playwright wrapper with anti-detection measures for Twitter/X."""

    def __init__(
        self,
        session_path: Path,
        user_data_dir: Path,
        headless: bool = False,
        slow_mo_ms: int = 50,
        proxy_url: str = "",
        viewport_width: int = 1280,
        viewport_height: int = 900,
    ) -> None:
        self._session_path = session_path
        self._user_data_dir = user_data_dir
        self._headless = headless
        self._slow_mo_ms = slow_mo_ms
        self._proxy_url = proxy_url
        self._viewport_width = viewport_width
        self._viewport_height = viewport_height

        self._pw: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    @property
    def page(self) -> Page:
        if self._page is None:
            raise RuntimeError("Browser not launched -- call launch() first")
        return self._page

    async def launch(self) -> Page:
        self._stealth = Stealth(
            navigator_platform_override="MacIntel",
        )
        self._stealth_cm = self._stealth.use_async(async_playwright())
        self._pw = await self._stealth_cm.__aenter__()

        launch_kwargs: dict[str, object] = {
            "headless": self._headless,
            "slow_mo": self._slow_mo_ms,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--no-first-run",
                "--no-default-browser-check",
            ],
        }
        if self._proxy_url:
            launch_kwargs["proxy"] = {"server": self._proxy_url}

        self._browser = await self._pw.chromium.launch(**launch_kwargs)  # type: ignore[arg-type]

        context_kwargs: dict[str, object] = {
            "viewport": {
                "width": self._viewport_width,
                "height": self._viewport_height,
            },
            "user_agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "locale": "en-US",
            "timezone_id": "America/New_York",
        }

        if self._session_path.exists():
            context_kwargs["storage_state"] = str(self._session_path)
            logger.info("Restoring session from %s", self._session_path)

        self._context = await self._browser.new_context(**context_kwargs)  # type: ignore[arg-type]
        self._page = await self._context.new_page()

        return self._page

    async def close(self) -> None:
        if self._context is not None:
            await self.save_session()
            try:
                await self._context.close()
            except Exception:
                logger.debug("Context already closed", exc_info=True)
        if self._browser is not None:
            try:
                await self._browser.close()
            except Exception:
                logger.debug("Browser already closed", exc_info=True)
        if hasattr(self, "_stealth_cm") and self._stealth_cm is not None:
            try:
                await self._stealth_cm.__aexit__(None, None, None)
            except Exception:
                logger.debug("Stealth cleanup failed", exc_info=True)
            self._stealth_cm = None
        self._page = None
        self._context = None
        self._browser = None
        self._pw = None

    async def save_session(self) -> None:
        if self._context is None:
            return
        try:
            state = await self._context.storage_state()
        except Exception:
            logger.warning("Could not save session (browser context already closed)")
            return
        self._session_path.parent.mkdir(parents=True, exist_ok=True)
        self._session_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
        logger.info("Session saved to %s", self._session_path)

    # ------------------------------------------------------------------
    # Login flow -- run once interactively, then reuse session
    # ------------------------------------------------------------------

    async def login_manual(self) -> None:
        """Open x.com and let the user log in manually."""
        page = self.page

        logger.info("Opening x.com -- please log in manually in the browser window.")
        await page.goto(_TWITTER_BASE, wait_until="load", timeout=60_000)
        await self._random_delay(2.0, 3.0)

        logger.info(
            "Waiting for you to log in... "
            "(you have up to 5 minutes -- complete login in the browser)"
        )
        await page.wait_for_url("**/home", timeout=300_000)

        await self.save_session()
        logger.info("Login successful, session saved.")

    async def login_with_cookies(self, auth_token: str, ct0: str) -> None:
        """Inject auth cookies and verify login."""
        if self._context is None:
            raise RuntimeError("Browser not launched")

        cookies = [
            {
                "name": "auth_token",
                "value": auth_token,
                "domain": ".x.com",
                "path": "/",
                "httpOnly": True,
                "secure": True,
                "sameSite": "None",
            },
            {
                "name": "ct0",
                "value": ct0,
                "domain": ".x.com",
                "path": "/",
                "httpOnly": False,
                "secure": True,
                "sameSite": "Lax",
            },
        ]
        await self._context.add_cookies(cookies)  # type: ignore[arg-type]
        logger.info("Cookies injected, verifying login...")

        page = self.page
        await page.goto(_TWITTER_HOME, wait_until="load", timeout=60_000)
        await self._random_delay(3.0, 5.0)

        url = page.url
        if "/login" in url or "/i/flow" in url:
            raise RuntimeError(
                "Cookie login failed -- Twitter redirected to login page. "
                "Cookies may be expired. Grab fresh ones from your browser."
            )

        await self.save_session()
        logger.info("Cookie login successful, session saved.")

    async def is_logged_in(self) -> bool:
        page = self.page
        try:
            await page.goto(
                _TWITTER_HOME, wait_until="domcontentloaded", timeout=30_000
            )
            await self._random_delay(3.0, 5.0)
            url = page.url
            if "/login" in url or "/i/flow" in url:
                return False
            # Check for a logged-in indicator on the page
            avatar = page.locator('div[data-testid="SideNav_AccountSwitcher_Button"]')
            try:
                await avatar.wait_for(state="visible", timeout=10_000)
                return True
            except Exception:
                return "/home" in url
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Navigation helpers
    # ------------------------------------------------------------------

    async def navigate(self, url: str, wait_until: str = "domcontentloaded") -> None:
        await self._random_delay(0.5, 2.0)
        await self.page.goto(url, wait_until=wait_until)  # type: ignore[arg-type]
        await self._random_delay(1.5, 3.5)
        await self._mouse_jitter()

    async def scroll_down(self, times: int = 1) -> None:
        for _ in range(times):
            delta = random.randint(300, 700)
            await self.page.mouse.wheel(0, delta)
            await self._random_delay(0.8, 2.5)
            await self._mouse_jitter()

    async def click(self, selector: str, timeout: int = 10_000) -> None:
        element = self.page.locator(selector).first
        await element.wait_for(state="visible", timeout=timeout)
        box = await element.bounding_box()
        if box:
            x = box["x"] + random.uniform(2, box["width"] - 2)
            y = box["y"] + random.uniform(2, box["height"] - 2)
            await self.page.mouse.click(x, y)
        else:
            await element.click()
        await self._random_delay(0.3, 1.0)

    async def type_text(self, selector: str, text: str, timeout: int = 10_000) -> None:
        element = self.page.locator(selector).first
        await element.wait_for(state="visible", timeout=timeout)
        await element.click()
        await self._random_delay(0.3, 0.8)
        await self._human_type(element, text)

    # ------------------------------------------------------------------
    # Reply posting
    # ------------------------------------------------------------------

    async def post_reply(self, post_url: str, reply_text: str) -> bool:
        """Navigate to a tweet and post a reply. Returns True on success."""
        await self.navigate(post_url)
        await self._random_delay(1.0, 3.0)
        await self.scroll_down(times=random.randint(0, 1))

        reply_box = self.page.locator('div[data-testid="tweetTextarea_0"]')
        try:
            await reply_box.wait_for(state="visible", timeout=10_000)
        except Exception:
            logger.warning("Reply box not found, trying click on reply area")
            reply_area = self.page.locator('div[data-testid="tweetTextarea_0_label"]')
            await reply_area.click()
            await self._random_delay(0.5, 1.0)
            reply_box = self.page.locator('div[data-testid="tweetTextarea_0"]')
            await reply_box.wait_for(state="visible", timeout=10_000)

        await reply_box.click()
        await self._random_delay(0.5, 1.2)

        for char in reply_text:
            await self.page.keyboard.type(char, delay=random.randint(30, 150))
            if random.random() < 0.03:
                await self._random_delay(0.3, 1.0)

        await self._random_delay(0.8, 2.0)

        reply_btn = self.page.locator('button[data-testid="tweetButtonInline"]')
        if not await reply_btn.is_visible():
            reply_btn = self.page.locator('button[data-testid="tweetButton"]')

        await self._force_click(reply_btn)
        await self._random_delay(2.0, 4.0)

        logger.info("Reply posted to %s", post_url)
        return True

    # ------------------------------------------------------------------
    # Thread posting
    # ------------------------------------------------------------------

    async def post_thread(self, tweets: list[str]) -> bool:
        """Compose and post a thread from the home timeline. Returns True on success."""
        if not tweets:
            return False

        await self.navigate(_TWITTER_HOME)
        await self._random_delay(1.5, 3.0)

        compose_btn = self.page.locator('a[data-testid="SideNav_NewTweet_Button"]')
        try:
            await compose_btn.wait_for(state="visible", timeout=10_000)
            await compose_btn.click()
        except Exception:
            compose_btn = self.page.locator('a[href="/compose/post"]')
            await compose_btn.click()
        await self._random_delay(1.0, 2.0)

        dialog = self.page.locator('div[role="dialog"][aria-modal="true"]')
        await dialog.wait_for(state="visible", timeout=10_000)

        tweet_box = dialog.locator('div[data-testid="tweetTextarea_0"]')
        await tweet_box.wait_for(state="visible", timeout=10_000)
        await tweet_box.click()
        await self._random_delay(0.3, 0.8)

        for char in tweets[0]:
            await self.page.keyboard.type(char, delay=random.randint(30, 120))
            if random.random() < 0.02:
                await self._random_delay(0.2, 0.6)

        await self._random_delay(0.5, 1.0)

        for idx, tweet_text in enumerate(tweets[1:], start=1):
            added = await self._click_add_tweet(dialog, idx)
            if not added:
                logger.error(
                    "Could not add tweet %d/%d to thread — posting what we have",
                    idx,
                    len(tweets) - 1,
                )
                break

            next_box = dialog.locator(f'div[data-testid="tweetTextarea_{idx}"]')
            await next_box.wait_for(state="visible", timeout=8_000)
            await next_box.click()
            await self._random_delay(0.3, 0.8)

            for char in tweet_text:
                await self.page.keyboard.type(char, delay=random.randint(30, 120))
                if random.random() < 0.02:
                    await self._random_delay(0.2, 0.6)

            await self._random_delay(0.5, 1.2)

        await self._random_delay(1.0, 2.0)

        post_all_btn = dialog.locator('button[data-testid="tweetButton"]')
        await post_all_btn.wait_for(state="visible", timeout=10_000)
        await self._force_click(post_all_btn)
        await self._random_delay(3.0, 5.0)

        try:
            await dialog.wait_for(state="hidden", timeout=10_000)
        except Exception:
            logger.warning("Compose dialog still visible after posting")

        logger.info("Thread posted (%d tweets)", len(tweets))
        return True

    async def _click_add_tweet(self, dialog: object, expected_idx: int) -> bool:
        """Click the '+' button to add a new tweet entry to the thread.

        Tries three strategies: direct testid click with force (bypasses
        overlay), broad page-level selector, and Tab-key navigation.
        Returns True if a new textarea appeared.
        """
        from playwright.async_api import Locator

        dlg: Locator = dialog  # type: ignore[assignment]
        textarea_sel = f'div[data-testid="tweetTextarea_{expected_idx}"]'

        # Strategy 1: force-click [data-testid="addButton"] inside dialog
        add_btn = dlg.locator('[data-testid="addButton"]')
        try:
            await add_btn.wait_for(state="visible", timeout=3_000)
            await self._force_click(add_btn)
            await self._random_delay(0.8, 1.5)
            if await dlg.locator(textarea_sel).count() > 0:
                return True
            logger.debug("addButton clicked but new textarea not found")
        except Exception:
            logger.debug("addButton not visible in dialog")

        # Strategy 2: page-wide selector (button may live outside the dialog)
        add_btn_page = self.page.locator('[data-testid="addButton"]')
        try:
            await add_btn_page.wait_for(state="visible", timeout=3_000)
            await self._force_click(add_btn_page)
            await self._random_delay(0.8, 1.5)
            if await dlg.locator(textarea_sel).count() > 0:
                return True
            logger.debug("Page-level addButton clicked but new textarea not found")
        except Exception:
            logger.debug("addButton not visible on page either")

        # Strategy 3: Tab navigation to reach the add button and press Enter.
        # In X's compose dialog the add-thread button is an SVG icon button
        # reachable by tabbing forward from the tweet textarea.
        logger.info("Trying Tab-navigation to reach add-tweet button")
        tab_count = 7 if expected_idx == 1 else 6
        for _ in range(tab_count):
            await self.page.keyboard.press("Tab")
            await self._random_delay(0.05, 0.15)
        await self.page.keyboard.press("Enter")
        await self._random_delay(1.0, 2.0)

        if await dlg.locator(textarea_sel).count() > 0:
            return True

        # Strategy 4: one more Tab count variant (X sometimes shifts focus order)
        for extra in (5, 8, 4):
            last_box = dlg.locator('div[data-testid^="tweetTextarea_"]').last
            await last_box.click()
            await self._random_delay(0.2, 0.4)
            for _ in range(extra):
                await self.page.keyboard.press("Tab")
                await self._random_delay(0.05, 0.15)
            await self.page.keyboard.press("Enter")
            await self._random_delay(1.0, 2.0)
            if await dlg.locator(textarea_sel).count() > 0:
                return True

        logger.error("All strategies to add tweet %d failed", expected_idx)
        return False

    # ------------------------------------------------------------------
    # Screenshot for debugging
    # ------------------------------------------------------------------

    async def screenshot(self, path: str | Path) -> None:
        await self.page.screenshot(path=str(path), full_page=False)

    # ------------------------------------------------------------------
    # Human-like behaviour primitives
    # ------------------------------------------------------------------

    async def _force_click(self, locator: object) -> None:
        """Click a button, bypassing overlay divs that intercept pointer events.

        Twitter/X renders full-screen overlay divs (position: fixed; inset: 0)
        that sit on top of buttons and block normal Playwright clicks.  We try
        three strategies in order: normal click, force-click (skips
        actionability checks), and a raw JS ``el.click()`` dispatch.
        """
        from playwright.async_api import Locator

        loc: Locator = locator  # type: ignore[assignment]
        try:
            await loc.click(timeout=5_000)
            return
        except Exception:
            logger.debug("Normal click intercepted, trying force click")

        try:
            await loc.click(force=True, timeout=5_000)
            return
        except Exception:
            logger.debug("Force click failed, falling back to JS click")

        await loc.evaluate("el => el.click()")

    async def _human_type(self, locator: object, text: str) -> None:
        """Type text character-by-character with realistic delays."""
        for char in text:
            delay_ms = random.randint(40, 180)
            await self.page.keyboard.type(char, delay=delay_ms)
            if random.random() < 0.02:
                await self._random_delay(0.2, 0.6)

    async def _random_delay(self, min_s: float, max_s: float) -> None:
        await asyncio.sleep(random.uniform(min_s, max_s))

    async def _mouse_jitter(self) -> None:
        """Small random mouse movements to look human."""
        for _ in range(random.randint(1, 3)):
            x = random.randint(100, self._viewport_width - 100)
            y = random.randint(100, self._viewport_height - 100)
            await self.page.mouse.move(x, y, steps=random.randint(5, 15))
            await self._random_delay(0.1, 0.4)

    # ------------------------------------------------------------------
    # Async context manager
    # ------------------------------------------------------------------

    async def __aenter__(self) -> StealthBrowser:
        await self.launch()
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()
